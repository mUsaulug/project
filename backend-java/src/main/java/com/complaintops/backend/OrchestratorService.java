package com.complaintops.backend;

import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.web.server.ResponseStatusException;
import lombok.RequiredArgsConstructor;
import java.util.List;
import java.util.ArrayList;
import java.util.UUID;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.Objects;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Service
@RequiredArgsConstructor
public class OrchestratorService {

    private static final Logger logger = LoggerFactory.getLogger(OrchestratorService.class);

    private final ComplaintRepository repository;
    private final WebClient.Builder webClientBuilder;

    @Value("${ai-service.url}")
    private String aiServiceUrl;

    /**
     * KVKK-Aware Complaint Analysis
     * FAIL-CLOSED: If masking fails, pipeline stops immediately.
     * Raw text NEVER goes to LLM, DB, or logs.
     */
    public Complaint analyzeComplaint(String rawText) {
        String requestId = UUID.randomUUID().toString();
        WebClient webClient = webClientBuilder.baseUrl(Objects.requireNonNull(aiServiceUrl)).build();
        logger.info("Starting complaint analysis. request_id={}", requestId);

        // 1. Mask PII - FAIL-CLOSED: No fallback to raw text
        DTOs.MaskingResponse maskResp;
        try {
            maskResp = webClient.post()
                    .uri("/mask")
                    .header("X-Request-ID", requestId)
                    .bodyValue(new DTOs.MaskingRequest(rawText))
                    .retrieve()
                    .bodyToMono(DTOs.MaskingResponse.class)
                    .block();
        } catch (Exception e) {
            // FAIL-CLOSED: Pipeline stops, create failed record without raw text
            logger.error("MASKING_FAILED: PII masking service unavailable. Raw text protected.");

            Complaint failedComplaint = new Complaint();
            failedComplaint.setMaskedText("[MASKING_ERROR - İçerik korumalı]");
            failedComplaint.setCategory("MANUAL_REVIEW");
            failedComplaint.setUrgency("HIGH");
            failedComplaint.setActionPlan("[\"Manuel inceleme gerekli: Maskeleme servisi hatası\"]");
            failedComplaint.setCustomerReplyDraft("Şikayetiniz alındı. Manuel inceleme için yönlendirildi.");
            failedComplaint.setStatus(ComplaintStatus.MASKING_FAILED);
            return repository.save(failedComplaint);
        }

        // Validate masking response
        if (maskResp == null || maskResp.getMaskedText() == null || maskResp.getMaskedText().isBlank()) {
            logger.error("MASKING_FAILED: Empty masking response. Raw text protected.");

            Complaint failedComplaint = new Complaint();
            failedComplaint.setMaskedText("[MASKING_ERROR - İçerik korumalı]");
            failedComplaint.setCategory("MANUAL_REVIEW");
            failedComplaint.setUrgency("HIGH");
            failedComplaint.setActionPlan("[\"Manuel inceleme gerekli: Boş maskeleme yanıtı\"]");
            failedComplaint.setCustomerReplyDraft("Şikayetiniz alındı. Manuel inceleme için yönlendirildi.");
            failedComplaint.setStatus(ComplaintStatus.MASKING_FAILED);
            return repository.save(failedComplaint);
        }

        String safeText = maskResp.getMaskedText();
        logger.info("PII masking successful. Masked entities: {}", maskResp.getMaskedEntities());

        // 2. Triage (with confidence tracking)
        DTOs.TriageResponseFull triageResp;
        try {
            triageResp = webClient.post()
                    .uri("/predict")
                    .header("X-Request-ID", requestId)
                    .bodyValue(new DTOs.TriageRequest(safeText))
                    .retrieve()
                    .bodyToMono(DTOs.TriageResponseFull.class)
                    .block();
        } catch (Exception e) {
            logger.warn("Triage failed, using defaults: {}", e.getMessage());
            triageResp = new DTOs.TriageResponseFull();
            triageResp.setCategory("MANUAL_REVIEW");
            triageResp.setUrgency("MEDIUM");
            triageResp.setNeedsHumanReview(true);
        }

        // 3. RAG Retrieval
        DTOs.RAGResponse ragResp;
        String ragStatus = "OK";
        try {
            ragResp = webClient.post()
                    .uri("/retrieve")
                    .header("X-Request-ID", requestId)
                    .bodyValue(new DTOs.RAGRequest(safeText))
                    .retrieve()
                    .bodyToMono(DTOs.RAGResponse.class)
                    .block();
        } catch (Exception e) {
            logger.warn("RAG failed: {}", e.getMessage());
            ragResp = new DTOs.RAGResponse();
            ragResp.setRelevantSnippets(new ArrayList<>());
            ragStatus = "UNAVAILABLE";
        }

        // 4. Generate Response
        DTOs.GenerateResponse genResp;
        String llmStatus = "OK";
        try {
            genResp = webClient.post()
                    .uri("/generate")
                    .header("X-Request-ID", requestId)
                    .bodyValue(new DTOs.GenerateRequest(
                            safeText,
                            triageResp.getCategory(),
                            triageResp.getUrgency(),
                            ragResp.getRelevantSnippets()))
                    .retrieve()
                    .bodyToMono(DTOs.GenerateResponse.class)
                    .block();
        } catch (Exception e) {
            logger.warn("Generation failed: {}", e.getMessage());
            genResp = new DTOs.GenerateResponse();
            genResp.setActionPlan(List.of("Sistem Hatası: AI yanıt üretemedi. Manuel inceleme gerekli."));
            genResp.setCustomerReplyDraft("Şikayetiniz alındı. En kısa sürede size dönüş yapılacaktır.");
            genResp.setSources(new ArrayList<>());
            llmStatus = "TEMPLATE_FALLBACK";
        }

        // 5. Save to DB - NO RAW TEXT EVER
        Complaint complaint = new Complaint();
        // originalText KALDIRILDI - KVKK uyumu
        complaint.setMaskedText(safeText);
        complaint.setCategory(triageResp.getCategory());
        complaint.setUrgency(triageResp.getUrgency());

        ObjectMapper mapper = new ObjectMapper();
        try {
            complaint.setActionPlan(mapper.writeValueAsString(genResp.getActionPlan()));
        } catch (Exception e) {
            complaint.setActionPlan(String.valueOf(genResp.getActionPlan()));
        }

        // Save RAG sources for explainability
        try {
            complaint.setSources(mapper.writeValueAsString(genResp.getSources()));
        } catch (Exception e) {
            complaint.setSources("[]");
        }

        complaint.setCustomerReplyDraft(genResp.getCustomerReplyDraft());
        complaint.setStatus(ComplaintStatus.ANALYZED);

        // Human-in-the-Loop fields
        complaint.setNeedsHumanReview(triageResp.isNeedsHumanReview());
        complaint.setReviewId(triageResp.getReviewId());

        // Confidence scores
        complaint.setCategoryConfidence(triageResp.getCategoryConfidence());
        complaint.setUrgencyConfidence(triageResp.getUrgencyConfidence());

        // Graceful degradation status
        complaint.setRagStatus(ragStatus);
        complaint.setLlmStatus(llmStatus);

        logger.info(
                "Complaint analysis complete. request_id={} category={} urgency={} needs_review={} rag_status={} llm_status={}",
                requestId, triageResp.getCategory(), triageResp.getUrgency(), triageResp.isNeedsHumanReview(),
                ragStatus, llmStatus);

        return repository.save(complaint);
    }

    public List<Complaint> getAllComplaints() {
        return repository.findAll();
    }

    public Complaint getComplaint(Long id) {
        return repository.findById(Objects.requireNonNull(id))
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Complaint not found"));
    }
}
