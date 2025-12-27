package com.complaintops.backend;

import java.util.Objects;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.DisplayName;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * T2: /api/sikayet Schema Validation Test
 * Verifies Turkish response schema: kategori, oncelik, oneri
 */
@WebMvcTest(ComplaintController.class)
class SikayetSchemaTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private OrchestratorService orchestratorService;

    @Test
    @DisplayName("T2: /api/sikayet returns correct Turkish schema")
    void testSikayetSchemaValidation() throws Exception {
        // Arrange
        Complaint mockComplaint = new Complaint();
        mockComplaint.setId(1L);
        mockComplaint.setCategory("FRAUD_UNAUTHORIZED_TX");
        mockComplaint.setUrgency("HIGH");
        mockComplaint.setCustomerReplyDraft("Sayın müşterimiz, şikayetiniz incelenmektedir.");
        mockComplaint.setMaskedText("[MASKED_TCKN] hesabından işlem yapıldı.");
        mockComplaint.setStatus(ComplaintStatus.ANALYZED);

        when(orchestratorService.analyzeComplaint(anyString())).thenReturn(mockComplaint);

        // Act & Assert
        mockMvc.perform(post("/api/sikayet")
                .contentType(Objects.requireNonNull(MediaType.APPLICATION_JSON))
                .content("{\"metin\": \"Test şikayeti\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(1))
                .andExpect(jsonPath("$.kategori").value("DOLANDIRICILIK_YETKISIZ_ISLEM"))
                .andExpect(jsonPath("$.oncelik").value("YUKSEK"))
                .andExpect(jsonPath("$.oneri").isString())
                .andExpect(jsonPath("$.durum").value("ANALIZ_EDILDI"));
    }

    @Test
    @DisplayName("T2b: MASKING_FAILED status maps to Turkish")
    void testMaskingFailedStatusMapping() throws Exception {
        // Arrange
        Complaint failedComplaint = new Complaint();
        failedComplaint.setId(2L);
        failedComplaint.setCategory("MANUAL_REVIEW");
        failedComplaint.setUrgency("HIGH");
        failedComplaint.setCustomerReplyDraft("Şikayetiniz manuel inceleme için yönlendirildi.");
        failedComplaint.setMaskedText("[MASKING_ERROR]");
        failedComplaint.setStatus(ComplaintStatus.MASKING_FAILED);

        when(orchestratorService.analyzeComplaint(anyString())).thenReturn(failedComplaint);

        // Act & Assert
        mockMvc.perform(post("/api/sikayet")
                .contentType(Objects.requireNonNull(MediaType.APPLICATION_JSON))
                .content("{\"metin\": \"Test şikayeti\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.kategori").value("MANUEL_INCELEME"))
                .andExpect(jsonPath("$.oncelik").value("YUKSEK"))
                .andExpect(jsonPath("$.durum").value("MASKELEME_HATASI"));
    }

    @Test
    @DisplayName("T2c: All required fields present in response")
    void testAllRequiredFieldsPresent() throws Exception {
        // Arrange
        Complaint complaint = new Complaint();
        complaint.setId(3L);
        complaint.setCategory("TRANSFER_DELAY");
        complaint.setUrgency("MEDIUM");
        complaint.setCustomerReplyDraft("EFT işleminiz takip edilmektedir.");
        complaint.setMaskedText("EFT gecikmesi");
        complaint.setStatus(ComplaintStatus.ANALYZED);

        when(orchestratorService.analyzeComplaint(anyString())).thenReturn(complaint);

        // Act & Assert: Verify all 5 fields exist
        mockMvc.perform(post("/api/sikayet")
                .contentType(Objects.requireNonNull(MediaType.APPLICATION_JSON))
                .content("{\"metin\": \"EFT param gelmedi\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").exists())
                .andExpect(jsonPath("$.kategori").exists())
                .andExpect(jsonPath("$.oncelik").exists())
                .andExpect(jsonPath("$.oneri").exists())
                .andExpect(jsonPath("$.durum").exists());
    }
}
