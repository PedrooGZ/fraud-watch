import { useEffect, useRef, useState } from "react";
import { api } from "../../services/api";
import Button from "../ui/Button";

const MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024;

function readDownloadFilename(headers, fallback) {
  const contentDisposition = headers.get("content-disposition") || "";
  const match = contentDisposition.match(/filename=\"?([^\";]+)\"?/i);
  return match?.[1] || fallback;
}

function triggerCsvDownload(blob, filename) {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

export default function CsvUploadModal({ open, onClose, onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [uploadResult, setUploadResult] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (!open) return undefined;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [open]);

  const handleSelectFile = (nextFile) => {
    setFile(nextFile);
    setErrorMessage("");
    setSuccessMessage("");
    setUploadResult(null);
  };

  const handleAnalyze = async () => {
    if (!file) {
      setErrorMessage("Selecciona un archivo CSV antes de analizar.");
      return;
    }

    if (!file.name.toLowerCase().endsWith(".csv")) {
      setErrorMessage("El archivo debe tener extensión .csv.");
      return;
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      setErrorMessage("El archivo supera el tamaño máximo permitido (20MB).");
      return;
    }

    setErrorMessage("");
    setSuccessMessage("");
    setUploadResult(null);
    setIsUploading(true);

    try {
      const result = await api.uploadBatchCsv(file);
      setUploadResult(result);
      setSuccessMessage("CSV procesado correctamente.");
      if (typeof onUploadSuccess === "function") {
        onUploadSuccess(result);
      }
    } catch (error) {
      setErrorMessage(
        error?.message
          || "No se pudo procesar el CSV. El archivo debe tener columnas Time, V1...V28 y Amount.",
      );
      setSuccessMessage("");
      setUploadResult(null);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDownloadResults = async () => {
    if (!uploadResult?.batch_job_id) return;

    setIsDownloading(true);
    setErrorMessage("");

    try {
      const response = await api.downloadBatchResults(uploadResult.batch_job_id);
      const filename = readDownloadFilename(
        response.headers,
        `batch_job_${uploadResult.batch_job_id}_results.csv`,
      );
      triggerCsvDownload(response.blob, filename);
    } catch (error) {
      setErrorMessage(error?.message || "No se pudieron descargar los resultados.");
    } finally {
      setIsDownloading(false);
    }
  };

  if (!open) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-panel" onClick={(event) => event.stopPropagation()}>
        <h2 style={{ marginTop: 0 }}>Subir CSV</h2>
        <p style={{ marginTop: 0, color: "var(--text-soft)" }}>
          Carga transacciones y lanza el análisis.
        </p>

        <div className="dropzone">
          <p style={{ fontSize: 32, marginBottom: 8 }}>CSV · max. 20MB</p>
          <p>Arrastra y suelta el archivo aquí o selecciónalo desde tu equipo.</p>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,text/csv"
            style={{ display: "none" }}
            onChange={(event) => handleSelectFile(event.target.files?.[0] || null)}
          />
          <Button type="button" onClick={() => fileInputRef.current?.click()}>
            Elegir archivo
          </Button>

          {file ? (
            <p style={{ marginTop: 10, color: "var(--text-soft)" }}>
              Seleccionado: {file.name}
            </p>
          ) : null}
        </div>

        {isUploading ? (
          <p className="notice" style={{ marginTop: 14 }}>
            Procesando CSV...
          </p>
        ) : null}
        {errorMessage ? (
          <p className="notice error" style={{ marginTop: 14 }}>
            {errorMessage}
          </p>
        ) : null}
        {successMessage ? (
          <p className="notice success" style={{ marginTop: 14 }}>
            {successMessage}
          </p>
        ) : null}

        {uploadResult ? (
          <div className="card" style={{ marginTop: 14 }}>
            <h3 className="section-title">Resumen de procesamiento</h3>
            <div className="table-like">
              <div className="data-row"><strong>Batch job ID</strong><span>{uploadResult.batch_job_id}</span></div>
              <div className="data-row"><strong>Total filas</strong><span>{uploadResult.total_rows}</span></div>
              <div className="data-row"><strong>Válidas</strong><span>{uploadResult.valid_rows}</span></div>
              <div className="data-row"><strong>Inválidas</strong><span>{uploadResult.invalid_rows}</span></div>
              <div className="data-row"><strong>Alertas</strong><span>{uploadResult.review_count}</span></div>
              <div className="data-row"><strong>Threshold</strong><span>{uploadResult.threshold_cost}</span></div>
              <div className="data-row"><strong>Max alerts</strong><span>{uploadResult.max_alerts}</span></div>
            </div>
          </div>
        ) : null}

        <div style={{ marginTop: 20, display: "grid", gap: 10 }}>
          <Button
            variant="primary"
            block
            type="button"
            onClick={handleAnalyze}
            disabled={isUploading}
          >
            {isUploading ? "Analizando..." : "Analizar"}
          </Button>

          {uploadResult?.batch_job_id ? (
            <Button
              block
              type="button"
              onClick={handleDownloadResults}
              disabled={isDownloading}
            >
              {isDownloading ? "Descargando..." : "Descargar resultados"}
            </Button>
          ) : null}

          <Button block type="button" onClick={onClose}>
            Cerrar
          </Button>
        </div>
      </div>
    </div>
  );
}
