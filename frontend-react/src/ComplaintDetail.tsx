import React, { useState, useEffect } from 'react';

interface ComplaintDetailProps {
    id: number;
    onBack: () => void;
}

export default function ComplaintDetail({ id, onBack }: ComplaintDetailProps) {
    const [complaint, setComplaint] = useState<any>(null);
    const [analyzing, setAnalyzing] = useState(false);

    useEffect(() => {
        fetch(`http://localhost:8080/api/complaints/${id}`)
            .then(res => res.json())
            .then(data => setComplaint(data));
    }, [id]);

    const handleAnalyze = () => {
        setAnalyzing(true);
        fetch('http://localhost:8080/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: complaint.maskedText })
        })
            .then(res => res.json())
            .then(data => setComplaint(data))
            .finally(() => setAnalyzing(false));
    };

    if (!complaint) return <p>Loading detail...</p>;

    return (
        <div>
            <button onClick={onBack}>&larr; Back to List</button>
            <h2>Complaint #{complaint.id}</h2>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                <div style={{ padding: '10px', border: '1px solid #ccc' }}>
                    <h3>Complaint</h3>
                    <p><strong>Status:</strong> {complaint.status}</p>
                    <div style={{ whiteSpace: 'pre-wrap', background: '#f9f9f9', padding: '10px' }}>
                        {complaint.maskedText}
                    </div>
                    {complaint.status === 'NEW' && (
                        <button
                            onClick={handleAnalyze}
                            disabled={analyzing}
                            style={{ marginTop: '10px', padding: '10px 20px', background: 'blue', color: 'white', border: 'none', cursor: 'pointer' }}
                        >
                            {analyzing ? 'Analyzing (AI)...' : 'ANALYZE WITH COPILOT'}
                        </button>
                    )}
                </div>

                <div style={{ padding: '10px', border: '1px solid #ccc', background: '#efffef' }}>
                    <h3>Copilot Suggestions</h3>
                    {complaint.status === 'NEW' ? (
                        <p><i>Click Analyze to generate suggestions.</i></p>
                    ) : (
                        <div>
                            <p><strong>Category:</strong> {complaint.category}</p>
                            <p><strong>Urgency:</strong> {complaint.urgency}</p>
                            <hr />
                            <h4>Action Plan</h4>
                            <pre style={{ fontFamily: 'inherit' }}>{complaint.actionPlan}</pre>
                            <hr />
                            <h4>Draft Reply</h4>
                            <textarea
                                rows={10}
                                style={{ width: '100%' }}
                                value={complaint.customerReplyDraft}
                                readOnly
                            />
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
