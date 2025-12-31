
import React from 'react';
import { ComplaintData, CustomerSegment } from '../types';
import { Icons } from '../constants';
import KVKKBadge from './KVKKBadge';

interface Props {
  data: ComplaintData;
}

const SmartComplaintViewer: React.FC<Props> = ({ data }) => {
  const getSegmentBadge = (segment: CustomerSegment) => {
    switch (segment) {
      case CustomerSegment.VIP_PLATINUM:
        return 'bg-indigo-600 text-white shadow-sm ring-1 ring-indigo-700';
      case CustomerSegment.GOLD:
        return 'bg-amber-500 text-white';
      default:
        return 'bg-slate-200 text-slate-700';
    }
  };

  const renderMaskedText = () => {
    // If maskedText is empty/loading
    if (!data.maskedText || data.maskedText === "Yükleniyor...") return data.maskedText;

    const parts = data.maskedText.split(/(\[[A-Z_]+\])/);
    return parts.map((part, i) => {
      const isTag = part.startsWith('[') && part.endsWith(']');
      if (isTag) {
        return (
          <span
            key={i}
            className="group relative inline-block mx-1 px-1.5 py-0.5 rounded bg-amber-100 text-amber-900 font-mono text-xs border border-amber-200 cursor-help"
          >
            {part}
            <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-max px-2 py-1 bg-slate-900 text-white text-[10px] rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
              PII Masked: {part.slice(1, -1)}
            </span>
          </span>
        );
      }
      return <span key={i}>{part}</span>;
    });
  };

  return (
    <div className="flex flex-col h-full overflow-y-auto">
      {/* Customer Profile Header */}
      <div className="p-6 border-b bg-zinc-50/50">
        <div className="flex justify-between items-start mb-4">
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-slate-900">{data.customerName}</h2>
              <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${getSegmentBadge(data.customerSegment)}`}>
                {data.customerSegment}
              </span>
            </div>
            <p className="text-xs text-slate-500">12 Yıllık Müşteri • İstanbul / TR</p>
          </div>
          <div className="text-right">
            <p className="text-xs font-mono text-slate-400">{data.id}</p>
            <p className="text-xs text-slate-500 mt-1">🕒 {new Date(data.timestamp).toLocaleTimeString()}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 mt-4">
          <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-sm">
            <p className="text-[10px] text-slate-400 font-bold uppercase mb-1">Risk Skoru</p>
            <p className="text-sm font-bold text-emerald-600">Düşük (12/100)</p>
          </div>
          <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-sm">
            <p className="text-[10px] text-slate-400 font-bold uppercase mb-1">Kullanım</p>
            <p className="text-sm font-bold text-slate-700">6 Aktif Kart</p>
          </div>
        </div>
      </div>

      {/* Complaint Content */}
      <div className="p-6 flex-1 flex flex-col gap-6">
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-tight flex items-center gap-2">
              <Icons.Search /> Şikayet İçeriği
            </h3>
            <KVKKBadge />
          </div>

          {/* Security Alert if Masking Failed */}
          {data.maskedText?.includes("MASKING_ERROR") && (
            <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg flex gap-2 items-center text-red-700 text-xs font-bold">
              <Icons.Alert />
              <span>KRİTİK: Maskeleme servisi yanıt vermedi. İçerik güvenlik nedeniyle gizlendi.</span>
            </div>
          )}

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm leading-relaxed text-sm text-slate-800 font-medium">
            {renderMaskedText()}
          </div>
          <p className="mt-2 text-[10px] text-slate-400 text-center flex items-center justify-center gap-1">
            <Icons.Shield /> Bu görüntü KVKK kapsamında denetlenmektedir.
          </p>
        </div>

        {/* Audit Logs */}
        <div className="mt-auto">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3 flex items-center gap-2">
            <Icons.History /> Geçmiş ve Loglar
          </h3>
          <div className="space-y-3">
            <div className="flex gap-3 text-xs">
              <div className="w-1.5 h-1.5 rounded-full bg-slate-300 mt-1" />
              <div>
                <p className="text-slate-600 font-medium">Önceki Şikayet Kapandı: <span className="text-slate-400">#CMP-2023-45</span></p>
                <p className="text-slate-400 text-[10px]">14 Ocak 2024</p>
              </div>
            </div>
            <div className="flex gap-3 text-xs">
              <div className="w-1.5 h-1.5 rounded-full bg-slate-300 mt-1" />
              <div>
                <p className="text-slate-600 font-medium">CRM Notu Eklendi: <span className="text-slate-400">Müşteri iade talep etti.</span></p>
                <p className="text-slate-400 text-[10px]">02 Şubat 2024</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SmartComplaintViewer;
