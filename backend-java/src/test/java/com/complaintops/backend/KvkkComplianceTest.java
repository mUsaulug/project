package com.complaintops.backend;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.springframework.web.reactive.function.client.WebClient;

import reactor.core.publisher.Mono;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.*;

/**
 * P0 Test Suite: KVKK Compliance Tests
 * T1: Fail-Closed - Masking failure must not leak raw text
 * T2: Schema validation - /api/sikayet returns correct TR fields
 * T3: No-raw-persist - DB never stores original text
 */
@SuppressWarnings("null")
class KvkkComplianceTest {

    @Mock
    private ComplaintRepository repository;

    @Mock
    private WebClient.Builder webClientBuilder;

    @Mock
    private WebClient webClient;

    @Mock
    private WebClient.RequestBodyUriSpec requestBodyUriSpec;

    @Mock
    private WebClient.RequestBodySpec requestBodySpec;

    @Mock
    private WebClient.ResponseSpec responseSpec;

    @Mock
    private WebClient.RequestHeadersSpec<?> requestHeadersSpec;

    private OrchestratorService orchestratorService;

    @BeforeEach

    void setUp() {
        MockitoAnnotations.openMocks(this);

        when(webClientBuilder.baseUrl(anyString())).thenReturn(webClientBuilder);
        when(webClientBuilder.build()).thenReturn(webClient);
        when(webClient.post()).thenReturn(requestBodyUriSpec);
        when(requestBodyUriSpec.uri(anyString())).thenReturn(requestBodySpec);
        doReturn(requestHeadersSpec).when(requestBodySpec).bodyValue(any());
        when(requestHeadersSpec.retrieve()).thenReturn(responseSpec);

        orchestratorService = new OrchestratorService(repository, webClientBuilder);

        // Use reflection to set the aiServiceUrl
        try {
            var field = OrchestratorService.class.getDeclaredField("aiServiceUrl");
            field.setAccessible(true);
            field.set(orchestratorService, "http://localhost:8000");
        } catch (Exception e) {
            fail("Could not set aiServiceUrl");
        }
    }

    @Test
    @DisplayName("T1: Fail-Closed - Masking failure creates MASKING_FAILED record without raw text")
    void testFailClosedMaskingFailure() {
        // Arrange: Masking service throws exception
        String rawPiiText = "Adım Ahmet Yılmaz, TC: 12345678901, IBAN: TR123456789012345678901234";

        when(responseSpec.bodyToMono(DTOs.MaskingResponse.class))
                .thenReturn(Mono.error(new RuntimeException("Connection refused")));

        when(repository.save(any(Complaint.class))).thenAnswer(invocation -> {
            Complaint c = invocation.getArgument(0);
            c.setId(1L);
            return c;
        });

        // Act
        Complaint result = orchestratorService.analyzeComplaint(rawPiiText);

        // Assert: FAIL-CLOSED behavior
        assertNotNull(result);
        assertEquals(ComplaintStatus.MASKING_FAILED, result.getStatus());
        assertEquals("MANUAL_REVIEW", result.getCategory());
        assertEquals("HIGH", result.getUrgency());

        // CRITICAL: Raw text must NOT be in the result
        assertFalse(result.getMaskedText().contains("Ahmet"));
        assertFalse(result.getMaskedText().contains("12345678901"));
        assertFalse(result.getMaskedText().contains("TR123456789012345678901234"));
        assertTrue(result.getMaskedText().contains("MASKING_ERROR"));

        // Verify no further AI calls were made after masking failure
        verify(responseSpec, times(1)).bodyToMono((Class<?>) any(Class.class));
    }

    @Test
    @DisplayName("T1b: Fail-Closed - Empty masking response creates MASKING_FAILED record")
    void testFailClosedEmptyMaskingResponse() {
        // Arrange: Masking returns null/empty
        String rawPiiText = "Kredi kartım çalındı, kart no: 4111111111111111";

        DTOs.MaskingResponse emptyResponse = new DTOs.MaskingResponse();
        emptyResponse.setMaskedText(null);

        when(responseSpec.bodyToMono(DTOs.MaskingResponse.class))
                .thenReturn(Mono.just(emptyResponse));

        when(repository.save(any(Complaint.class))).thenAnswer(invocation -> {
            Complaint c = invocation.getArgument(0);
            c.setId(1L);
            return c;
        });

        // Act
        Complaint result = orchestratorService.analyzeComplaint(rawPiiText);

        // Assert
        assertEquals(ComplaintStatus.MASKING_FAILED, result.getStatus());
        assertFalse(result.getMaskedText().contains("4111111111111111"));
    }

    @Test
    @DisplayName("T3: No-Raw-Persist - Complaint entity has no originalText field")
    void testNoOriginalTextInEntity() {
        // Verify via reflection that originalText field does not exist
        boolean hasOriginalTextField = false;
        for (var field : Complaint.class.getDeclaredFields()) {
            if (field.getName().equals("originalText")) {
                hasOriginalTextField = true;
                break;
            }
        }

        assertFalse(hasOriginalTextField,
                "KVKK VIOLATION: Complaint entity must not have originalText field");
    }

    @Test
    @DisplayName("T3b: No-Raw-Persist - Successful flow never saves raw text")
    void testSuccessfulFlowNoRawText() {
        // Arrange
        String rawText = "Hesabımdan izinsiz 5000 TL çekildi, TC: 98765432109";
        String maskedText = "Hesabımdan izinsiz 5000 TL çekildi, TC: [MASKED_TCKN]";

        // Mock masking success
        DTOs.MaskingResponse maskResp = new DTOs.MaskingResponse();
        maskResp.setMaskedText(maskedText);
        maskResp.setMaskedEntities(List.of("TCKN"));

        when(responseSpec.bodyToMono(DTOs.MaskingResponse.class))
                .thenReturn(Mono.just(maskResp));

        // Mock triage
        DTOs.TriageResponse triageResp = new DTOs.TriageResponse();
        triageResp.setCategory("FRAUD_UNAUTHORIZED_TX");
        triageResp.setUrgency("HIGH");

        when(responseSpec.bodyToMono(DTOs.TriageResponse.class))
                .thenReturn(Mono.just(triageResp));

        // Mock RAG
        DTOs.RAGResponse ragResp = new DTOs.RAGResponse();
        ragResp.setRelevantSnippets(List.of());

        when(responseSpec.bodyToMono(DTOs.RAGResponse.class))
                .thenReturn(Mono.just(ragResp));

        // Mock generate
        DTOs.GenerateResponse genResp = new DTOs.GenerateResponse();
        genResp.setActionPlan(List.of("İşlem inceleniyor"));
        genResp.setCustomerReplyDraft("Şikayetiniz alındı.");

        when(responseSpec.bodyToMono(DTOs.GenerateResponse.class))
                .thenReturn(Mono.just(genResp));

        when(repository.save(any(Complaint.class))).thenAnswer(invocation -> {
            Complaint c = invocation.getArgument(0);
            c.setId(1L);

            // CRITICAL ASSERTION: Saved complaint must not contain raw text
            assertFalse(c.getMaskedText().contains("98765432109"),
                    "KVKK VIOLATION: Raw TCKN found in maskedText");

            return c;
        });

        // Act
        Complaint result = orchestratorService.analyzeComplaint(rawText);

        // Assert
        assertNotNull(result);
        assertEquals(ComplaintStatus.ANALYZED, result.getStatus());
        assertTrue(result.getMaskedText().contains("[MASKED_TCKN]"));
        verify(repository, times(1)).save(any(Complaint.class));
    }
}
