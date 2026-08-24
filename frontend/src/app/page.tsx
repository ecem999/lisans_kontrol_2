"use client";
import { useState } from 'react';
import DynamicForm from '@/components/DynamicForm';
import UploadZone from '@/components/UploadZone';
import BatchUploadZone from '@/components/BatchUploadZone';
import StatusCard from '@/components/StatusCard';
import { ShieldCheck, FileText, Camera, Layers } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8002";

export default function Home() {
  const [activeTab, setActiveTab] = useState<'manual' | 'ocr' | 'batch'>('manual');
  const [result, setResult] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleManualSubmit = async (data: any) => {
    setIsLoading(true);
    setResult(null);
    try {
      const res = await fetch(`${API_URL}/api/verify/manual`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      });
      const resData = await res.json();
      if (!res.ok) throw new Error(resData.detail?.message || resData.detail || "Doğrulama hatası");
      setResult(resData);
    } catch (error: any) {
      setResult({ status: "INVALID", label: "İstek Başarısız", message: error.message });
    } finally {
      setIsLoading(false);
    }
  };

  const handleImageUpload = async (formData: FormData) => {
    setIsLoading(true);
    setResult(null);
    try {
      const res = await fetch(`${API_URL}/api/verify/image`, {
        method: "POST",
        body: formData
      });
      const resData = await res.json();
      if (!res.ok) throw new Error(resData.detail?.message || resData.detail || "Görsel işleme hatası");
      setResult(resData);
    } catch (error: any) {
      setResult({ status: "INVALID", label: "İstek Başarısız", message: error.message });
    } finally {
      setIsLoading(false);
    }
  };

  const handleBatchUpload = async (formData: FormData) => {
    setIsLoading(true);
    setResult(null);
    try {
      const res = await fetch(`${API_URL}/api/verify/batch`, {
        method: "POST",
        body: formData
      });
      
      if (!res.ok) {
          const resData = await res.json().catch(() => null);
          throw new Error(resData?.detail?.message || resData?.detail || "Toplu işlem hatası");
      }
      
      // Blob olarak indir
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "veritabani_log.xlsx";
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      
      setResult({ 
          status: "VALID", 
          label: "İşlem Tamamlandı", 
          message: "Toplu log dosyası başarıyla indirildi. Dosyayı kontrol edebilirsiniz." 
      });
    } catch (error: any) {
      setResult({ status: "INVALID", label: "İstek Başarısız", message: error.message });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white font-sans selection:bg-blue-500/30 relative overflow-hidden">
      
      {/* Decorative Blur Backgrounds */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-600/10 blur-[120px] rounded-full pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-indigo-600/10 blur-[120px] rounded-full pointer-events-none" />

      <div className="max-w-3xl mx-auto pt-16 pb-24 px-4 sm:px-6 relative z-10">
        
        {/* Header */}
        <div className="text-center mb-12 flex flex-col items-center gap-4 animate-in fade-in slide-in-from-top-4 duration-500">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-[0_0_30px_rgba(59,130,246,0.3)]">
            <ShieldCheck className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-4xl sm:text-5xl font-extrabold bg-gradient-to-r from-blue-100 via-white to-blue-100 bg-clip-text text-transparent tracking-tight">
            Lisans Doğrulama
          </h1>
          <p className="text-slate-400 text-sm sm:text-base max-w-xl font-medium leading-relaxed">
            Avrupa Birliği (İspanya, Fransa, İtalya) Turist Rehberi Lisans Doğrulama Motoru. Manuel giriş yapın veya yaka kartını yapay zekaya okutun.
          </p>
        </div>

        {/* Glass Container */}
        <div className="bg-slate-900/40 border border-white/10 backdrop-blur-2xl rounded-3xl p-6 sm:p-8 shadow-2xl animate-in zoom-in-95 duration-500">
          
          {/* Tabs */}
          <div className="flex bg-black/40 rounded-xl p-1.5 mb-8 border border-white/5">
            <button 
              onClick={() => { setActiveTab('manual'); setResult(null); }} 
              className={`flex-1 flex justify-center items-center gap-2 py-3 rounded-lg text-sm font-semibold transition-all duration-300 ${activeTab === 'manual' ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}
            >
              <FileText className="w-4 h-4" /> Manuel Giriş
            </button>
            <button 
              onClick={() => { setActiveTab('ocr'); setResult(null); }} 
              className={`flex-1 flex justify-center items-center gap-2 py-3 rounded-lg text-sm font-semibold transition-all duration-300 ${activeTab === 'ocr' ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}
            >
              <Camera className="w-4 h-4" /> Görsel Yükle (OCR)
            </button>
            <button 
              onClick={() => { setActiveTab('batch'); setResult(null); }} 
              className={`flex-1 flex justify-center items-center gap-2 py-3 rounded-lg text-sm font-semibold transition-all duration-300 ${activeTab === 'batch' ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}
            >
              <Layers className="w-4 h-4" /> Toplu İşlem (Batch)
            </button>
          </div>

          {/* Active Component */}
          <div className="min-h-[300px]">
            {activeTab === 'manual' && <DynamicForm onSubmit={handleManualSubmit} isLoading={isLoading} />}
            {activeTab === 'ocr' && <UploadZone onUpload={handleImageUpload} isLoading={isLoading} />}
            {activeTab === 'batch' && <BatchUploadZone onUpload={handleBatchUpload} isLoading={isLoading} />}
          </div>

        </div>

        {/* Result Area */}
        {result && (
          <StatusCard result={result} onReset={() => setResult(null)} />
        )}
        
      </div>
    </div>
  );
}
