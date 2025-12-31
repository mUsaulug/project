package com.complaintops.backend;

import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import lombok.RequiredArgsConstructor;
import lombok.Data;
import lombok.AllArgsConstructor;
import lombok.NoArgsConstructor;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.List;
import java.util.ArrayList;

@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class ComplaintController {

    private final OrchestratorService orchestratorService;
    private final ComplaintRepository complaintRepository;
    private final ComplaintEditRepository editRepository;
    private final org.springframework.web.reactive.function.client.WebClient.Builder webClientBuilder;

    @org.springframework.beans.factory.annotation.Value("${ai-service.url}")
    private String aiServiceUrl;

    @GetMapping("/complaints")
    public List<Complaint> getAllComplaints() {
        return orchestratorService.getAllComplaints();
    }

    @GetMapping("/complaints/{id}")
    public Complaint getComplaint(@PathVariable Long id) {
        return orchestratorService.getComplaint(id);
    }

    @PostMapping("/analyze")
    public Complaint analyzeComplaint(@RequestBody ComplaintRequest request) {
        return orchestratorService.analyzeComplaint(request.getText());
    }

    /**
     * /api/sikayet - Türkçe API kontratı (Sunum MVP)
     * Response: { kategori, oncelik, oneri }
     */
    @PostMapping("/sikayet")
    public ResponseEntity<SikayetResponse> sikayetAnaliz(@RequestBody SikayetRequest request) {
        Complaint complaint = orchestratorService.analyzeComplaint(request.getMetin());

        // Map to Turkish response schema
        SikayetResponse response = new SikayetResponse();
        response.setId(complaint.getId());
        response.setKategori(mapCategoryToTurkish(complaint.getCategory()));
        response.setOncelik(mapUrgencyToTurkish(complaint.getUrgency()));
        response.setOneri(buildOneri(complaint));
        response.setDurum(mapStatusToTurkish(complaint.getStatus()));
        response.setKaynaklar(parseKaynaklar(complaint.getSources()));
        response.setMaskedText(complaint.getMaskedText());

        // Human-in-the-Loop fields
        response.setInsanIncelemesiGerekli(
                complaint.getNeedsHumanReview() != null ? complaint.getNeedsHumanReview() : false);
        response.setReviewId(complaint.getReviewId());

        // Confidence scores
        response.setGuvenSkorlari(new GuvenSkorlari(
                complaint.getCategoryConfidence(),
                complaint.getUrgencyConfidence()));

        // Graceful degradation status
        response.setSistemDurumu(new SistemDurumu(
                complaint.getRagStatus(),
                complaint.getLlmStatus()));

        return ResponseEntity.ok(response);
    }

    // ============== SIMILAR COMPLAINTS ==============

    @GetMapping("/complaints/{id}/similar")
    public ResponseEntity<?> findSimilarComplaints(
            @PathVariable Long id,
            @RequestParam(defaultValue = "5") int limit) {
        Complaint complaint = orchestratorService.getComplaint(id);

        try {
            var webClient = webClientBuilder.baseUrl(java.util.Objects.requireNonNull(aiServiceUrl)).build();
            var response = webClient.get()
                    .uri(uriBuilder -> uriBuilder
                            .path("/similar/{id}")
                            .queryParam("query_text", complaint.getMaskedText())
                            .queryParam("limit", limit)
                            .build(id))
                    .retrieve()
                    .bodyToMono(java.util.Map.class)
                    .block();
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            return ResponseEntity.ok(java.util.Map.of(
                    "similar_complaints", new ArrayList<>(),
                    "error", "Similarity service unavailable"));
        }
    }

    // ============== EDIT COMPLAINT ==============

    @PatchMapping("/complaints/{id}/edit")
    public ResponseEntity<Complaint> editComplaint(
            @PathVariable Long id,
            @RequestBody EditRequest request,
            @RequestHeader(value = "X-User-Id", required = false) String userId) {
        Complaint complaint = orchestratorService.getComplaint(id);

        // Track changes for audit
        if (request.getCustomerReplyDraft() != null) {
            ComplaintEdit edit = new ComplaintEdit();
            edit.setComplaintId(id);
            edit.setFieldName("customer_reply_draft");
            edit.setOldValue(complaint.getCustomerReplyDraft());
            edit.setNewValue(request.getCustomerReplyDraft());
            edit.setEditedBy(userId != null ? userId : "anonymous");
            edit.setEditReason(request.getEditReason());
            editRepository.save(edit);

            complaint.setCustomerReplyDraft(request.getCustomerReplyDraft());
        }

        return ResponseEntity.ok(complaintRepository.save(java.util.Objects.requireNonNull(complaint)));
    }

    @GetMapping("/complaints/{id}/edit-history")
    public List<ComplaintEdit> getEditHistory(@PathVariable Long id) {
        return editRepository.findByComplaintIdOrderByEditedAtDesc(id);
    }

    // ============== APPROVE / REJECT ==============

    @PostMapping("/complaints/{id}/approve")
    public ResponseEntity<Complaint> approveComplaint(
            @PathVariable Long id,
            @RequestBody(required = false) ApprovalRequest request) {
        Complaint complaint = orchestratorService.getComplaint(id);

        // If has review_id, call Python to update review status
        if (complaint.getReviewId() != null) {
            try {
                var webClient = webClientBuilder.baseUrl(java.util.Objects.requireNonNull(aiServiceUrl)).build();
                webClient.post()
                        .uri("/review/approve")
                        .bodyValue(java.util.Objects.requireNonNull(java.util.Map.of(
                                "review_id", complaint.getReviewId(),
                                "notes", request != null && request.getNotes() != null ? request.getNotes() : "")))
                        .retrieve()
                        .toBodilessEntity()
                        .block();
            } catch (Exception e) {
                // Log but don't fail - Python review is optional
            }
        }

        // Update complaint status
        complaint.setStatus(ComplaintStatus.RESOLVED);
        return ResponseEntity.ok(complaintRepository.save(complaint));
    }

    @PostMapping("/complaints/{id}/reject")
    public ResponseEntity<Complaint> rejectComplaint(
            @PathVariable Long id,
            @RequestBody(required = false) ApprovalRequest request) {
        Complaint complaint = orchestratorService.getComplaint(id);

        // If has review_id, call Python to update review status
        if (complaint.getReviewId() != null) {
            try {
                var webClient = webClientBuilder.baseUrl(java.util.Objects.requireNonNull(aiServiceUrl)).build();
                webClient.post()
                        .uri("/review/reject")
                        .bodyValue(java.util.Objects.requireNonNull(java.util.Map.of(
                                "review_id", complaint.getReviewId(),
                                "notes", request != null && request.getNotes() != null ? request.getNotes() : "")))
                        .retrieve()
                        .toBodilessEntity()
                        .block();
            } catch (Exception e) {
                // Log but don't fail
            }
        }

        // Keep status as NEW or set a REJECTED status if needed
        return ResponseEntity.ok(complaintRepository.save(complaint));
    }

    private String mapCategoryToTurkish(String category) {
        if (category == null)
            return "BELİRSİZ";
        return switch (category) {
            case "FRAUD_UNAUTHORIZED_TX" -> "DOLANDIRICILIK_YETKISIZ_ISLEM";
            case "CHARGEBACK_DISPUTE" -> "IADE_ITIRAZ";
            case "TRANSFER_DELAY" -> "TRANSFER_GECIKMESI";
            case "ACCESS_LOGIN_MOBILE" -> "ERISIM_GIRIS_MOBIL";
            case "CARD_LIMIT_CREDIT" -> "KART_LIMIT_KREDI";
            case "INFORMATION_REQUEST" -> "BILGI_TALEBI";
            case "CAMPAIGN_POINTS_REWARDS" -> "KAMPANYA_PUAN_ODUL";
            case "MANUAL_REVIEW" -> "MANUEL_INCELEME";
            default -> category;
        };
    }

    private String mapUrgencyToTurkish(String urgency) {
        if (urgency == null)
            return "ORTA";
        return switch (urgency.toUpperCase()) {
            case "HIGH" -> "YUKSEK";
            case "MEDIUM" -> "ORTA";
            case "LOW" -> "DUSUK";
            default -> urgency;
        };
    }

    private String mapStatusToTurkish(ComplaintStatus status) {
        if (status == null)
            return "YENI";
        return switch (status) {
            case NEW -> "YENI";
            case MASKING_FAILED -> "MASKELEME_HATASI";
            case ANALYZED -> "ANALIZ_EDILDI";
            case RESOLVED -> "COZUMLENDI";
        };
    }

    private String buildOneri(Complaint complaint) {
        // Combine action plan and reply draft into single recommendation
        StringBuilder oneri = new StringBuilder();
        if (complaint.getCustomerReplyDraft() != null && !complaint.getCustomerReplyDraft().isBlank()) {
            oneri.append(complaint.getCustomerReplyDraft());
        }
        return oneri.toString();
    }

    private List<KaynakItem> parseKaynaklar(String sourcesJson) {
        if (sourcesJson == null || sourcesJson.isBlank()) {
            return new ArrayList<>();
        }
        try {
            ObjectMapper mapper = new ObjectMapper();
            List<DTOs.SourceItem> sources = mapper.readValue(sourcesJson,
                    new TypeReference<List<DTOs.SourceItem>>() {
                    });
            return sources.stream()
                    .map(s -> new KaynakItem(
                            s.getDocName(),
                            s.getSource(),
                            s.getSnippet() != null && s.getSnippet().length() > 100
                                    ? s.getSnippet().substring(0, 100) + "..."
                                    : s.getSnippet()))
                    .toList();
        } catch (Exception e) {
            return new ArrayList<>();
        }
    }

    // Request/Response DTOs for /api/sikayet

    @Data
    static class ComplaintRequest {
        private String text;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class SikayetRequest {
        private String metin; // Şikayet metni
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class SikayetResponse {
        private Long id;

        @JsonProperty("kategori")
        private String kategori; // Kategori (TR)

        @JsonProperty("oncelik")
        private String oncelik; // Öncelik seviyesi (TR)

        @JsonProperty("oneri")
        private String oneri; // Çözüm önerisi

        @JsonProperty("durum")
        private String durum; // İşlem durumu

        @JsonProperty("kaynaklar")
        private List<KaynakItem> kaynaklar; // RAG kaynakları

        @JsonProperty("maskedText")
        private String maskedText; // Maskelenmiş metin

        @JsonProperty("insan_incelemesi_gerekli")
        private Boolean insanIncelemesiGerekli; // Human review needed?

        @JsonProperty("review_id")
        private String reviewId; // Review record ID

        @JsonProperty("guven_skorlari")
        private GuvenSkorlari guvenSkorlari; // Confidence scores

        @JsonProperty("sistem_durumu")
        private SistemDurumu sistemDurumu; // Graceful degradation status
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class KaynakItem {
        @JsonProperty("dokuman_adi")
        private String dokumanAdi;

        @JsonProperty("kaynak")
        private String kaynak;

        @JsonProperty("ozet")
        private String ozet;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class GuvenSkorlari {
        @JsonProperty("kategori")
        private Double kategori; // 0-1 confidence

        @JsonProperty("oncelik")
        private Double oncelik; // 0-1 confidence
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class SistemDurumu {
        @JsonProperty("rag_durumu")
        private String ragDurumu; // OK, UNAVAILABLE, ERROR

        @JsonProperty("llm_durumu")
        private String llmDurumu; // OK, TEMPLATE_FALLBACK, ERROR
    }

    // ============== NEW DTOs for Task B ==============

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class EditRequest {
        @JsonProperty("customer_reply_draft")
        private String customerReplyDraft;

        @JsonProperty("edit_reason")
        private String editReason;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ApprovalRequest {
        private String notes;
    }
}
