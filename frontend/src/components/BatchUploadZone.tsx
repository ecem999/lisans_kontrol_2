"use client";
import { useState, useRef } from "react";
import { Loader2, FileArchive } from "lucide-react";

interface BatchUploadZoneProps {
  onUpload: (formData: FormData) => void;
  isLoading: boolean;
}

export default function BatchUploadZone({ onUpload, isLoading }: BatchUploadZoneProps) {
  const [country, setCountry] = useState("spain");
  const [region, setRegion] = useState("auto");
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFiles = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const fileArray = Array.from(files);
    setSelectedFiles(fileArray);
  };

  const handleSubmit = () => {
    if (selectedFiles.length === 0) return;
    
    const formData = new FormData();
    formData.append("country", country);
    
    if (country === "spain" && region) {
        formData.append("region", region);
    }
    
    selectedFiles.forEach((file) => {
      formData.append("files", file);
    });
    
    onUpload(formData);
  };

  const borderClass = (dragState: boolean) => dragState 
    ? "border-blue-400 bg-blue-500/10 shadow-[0_0_20px_rgba(59,130,246,0.2)]" 
    : "border-white/20 hover:border-white/40 hover:bg-white/5";
    
  const inputClass = "w-full p-3.5 bg-white/5 backdrop-blur-md border border-white/10 rounded-xl focus:outline-none focus:border-blue-500/50 text-white transition-all";

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row gap-4">
        <select value={country} onChange={(e) => setCountry(e.target.value)} className={inputClass} disabled={isLoading}>
          <option value="spain" className="bg-slate-800">İspanya</option>
          <option value="france" className="bg-slate-800">Fransa</option>
          <option value="italy" className="bg-slate-800">İtalya</option>
        </select>
        
        {country === "spain" && (
          <select value={region} onChange={(e) => setRegion(e.target.value)} className={`${inputClass} animate-in fade-in`} disabled={isLoading}>
            <option value="auto" className="bg-slate-800 text-blue-400 font-bold">✨ Otomatik Algıla (Yapay Zeka)</option>
            <option value="" className="bg-slate-800">Bölge Seçiniz (Zorunlu)</option>
            <option value="andalucia" className="bg-slate-800">Endülüs (Andalucía)</option>
            <option value="aragon" className="bg-slate-800">Aragón</option>
            <option value="asturias" className="bg-slate-800">Asturias</option>
            <option value="baleares" className="bg-slate-800">Balear Adaları (Baleares)</option>
            <option value="canarias" className="bg-slate-800">Kanarya Adaları (Canarias)</option>
            <option value="cantabria" className="bg-slate-800">Cantabria</option>
            <option value="castilla_la_mancha" className="bg-slate-800">Kastilya-La Mancha</option>
            <option value="castilla_y_leon" className="bg-slate-800">Kastilya ve Leon</option>
            <option value="catalunya" className="bg-slate-800">Katalonya (Cataluña)</option>
            <option value="extremadura" className="bg-slate-800">Extremadura</option>
            <option value="galicia" className="bg-slate-800">Galiçya (Galicia)</option>
            <option value="madrid" className="bg-slate-800">Madrid</option>
            <option value="murcia" className="bg-slate-800">Murcia</option>
            <option value="navarra" className="bg-slate-800">Navarra</option>
            <option value="pais_vasco" className="bg-slate-800">Bask Bölgesi (País Vasco)</option>
            <option value="rioja" className="bg-slate-800">La Rioja</option>
            <option value="valencia" className="bg-slate-800">Valensiya (Comunidad Valenciana)</option>
            <option value="ceuta_melilla" className="bg-slate-800">Ceuta ve Melilla</option>
          </select>
        )}
      </div>

      <div 
        className={`relative border-2 border-dashed rounded-2xl p-12 flex flex-col items-center justify-center text-center transition-all cursor-pointer ${borderClass(isDragging)}`}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => { e.preventDefault(); setIsDragging(false); handleFiles(e.dataTransfer.files); }}
        onClick={() => !isLoading && fileInputRef.current?.click()}
      >
        <input 
            type="file" 
            multiple 
            className="hidden" 
            ref={fileInputRef} 
            onChange={(e) => handleFiles(e.target.files)} 
            accept=".zip, image/jpeg, image/png, image/webp" 
        />
        
        {isLoading ? (
          <div className="flex flex-col items-center gap-3 animate-in fade-in zoom-in-95 duration-300">
            <Loader2 className="w-12 h-12 text-blue-400 animate-spin" />
            <p className="text-blue-300 font-medium tracking-wide">Toplu İşlem Devam Ediyor Lütfen Bekleyin...</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <div className={`p-4 rounded-full transition-colors ${isDragging ? 'bg-blue-500/20 text-blue-400' : 'bg-white/10 text-slate-300'}`}>
              <FileArchive className="w-10 h-10" />
            </div>
            <p className="text-slate-200 font-medium text-lg">Toplu Resim veya ZIP dosyası sürükleyin</p>
            <p className="text-sm text-slate-400">veya <span className="text-blue-400 font-medium">seçmek için tıklayın</span></p>
            <p className="text-xs text-slate-500 mt-2 font-mono">.ZIP, JPG, PNG, WEBP (Çoklu Seçim)</p>
            
            {selectedFiles.length > 0 && (
                <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/20 rounded-xl w-full max-w-sm" onClick={(e) => e.stopPropagation()}>
                    <p className="text-blue-300 text-sm font-semibold mb-1">Seçilen Dosyalar:</p>
                    <p className="text-slate-300 text-xs truncate">
                        {selectedFiles.length === 1 ? selectedFiles[0].name : `${selectedFiles.length} adet dosya seçildi.`}
                    </p>
                </div>
            )}
          </div>
        )}
      </div>

      {!isLoading && selectedFiles.length > 0 && (
          <button 
            onClick={handleSubmit}
            className="w-full py-3.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold rounded-xl shadow-[0_0_20px_rgba(59,130,246,0.3)] transition-all transform hover:scale-[1.01]"
          >
            Yükle ve Doğrula
          </button>
      )}
    </div>
  );
}
