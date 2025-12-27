import React, { useEffect, useState } from 'react';

interface Complaint {
    id: number;
    originalText: string;
    category: string;
    urgency: string;
    status: string;
}

interface ComplaintListProps {
    onSelect: (id: number) => void;
}

export default function ComplaintList({ onSelect }: ComplaintListProps) {
    const [complaints, setComplaints] = useState<Complaint[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchComplaints();
    }, []);

    const fetchComplaints = () => {
        setLoading(true);
        fetch('http://localhost:8080/api/complaints')
            .then(res => res.json())
            .then(data => setComplaints(data))
            .catch(err => console.error("Error fetching complaints:", err))
            .finally(() => setLoading(false));
    };

    return (
        <div>
            <h2>Complaint Inbox</h2>
            <button onClick={fetchComplaints}>Refresh</button>
            {loading && <p>Loading...</p>}
            <table border={1} cellPadding={10} style={{ width: '100%', marginTop: '10px', borderCollapse: 'collapse' }}>
                <thead>
                    <tr style={{ backgroundColor: '#f2f2f2' }}>
                        <th>ID</th>
                        <th>Text (Summary)</th>
                        <th>Category</th>
                        <th>Urgency</th>
                        <th>Status</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    {complaints.map(c => (
                        <tr key={c.id}>
                            <td>{c.id}</td>
                            <td>{c.originalText.substring(0, 50)}...</td>
                            <td>{c.category || '-'}</td>
                            <td style={{ color: c.urgency === 'RED' ? 'red' : c.urgency === 'YELLOW' ? 'orange' : 'green' }}>
                                {c.urgency || '-'}
                            </td>
                            <td>{c.status}</td>
                            <td>
                                <button onClick={() => onSelect(c.id)}>View / Analyze</button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
