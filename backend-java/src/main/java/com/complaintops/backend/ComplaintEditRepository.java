package com.complaintops.backend;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface ComplaintEditRepository extends JpaRepository<ComplaintEdit, Long> {
    List<ComplaintEdit> findByComplaintIdOrderByEditedAtDesc(Long complaintId);
}
