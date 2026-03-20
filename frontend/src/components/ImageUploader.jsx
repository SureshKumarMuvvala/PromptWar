import React, { useState, useRef, useCallback } from 'react';

export default function ImageUploader({ onImageSelected }) {
  const [preview, setPreview] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleFile = useCallback(
    (file) => {
      if (!file || !file.type.startsWith('image/')) return;
      onImageSelected(file);
      const reader = new FileReader();
      reader.onload = (e) => setPreview(e.target.result);
      reader.readAsDataURL(file);
    },
    [onImageSelected]
  );

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      setIsDragOver(false);
      const file = e.dataTransfer.files[0];
      handleFile(file);
    },
    [handleFile]
  );

  const removeImage = () => {
    setPreview(null);
    onImageSelected(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <section className="card" aria-labelledby="image-upload-title">
      <div className="card__header">
        <span className="card__icon" role="img" aria-label="Camera icon">📷</span>
        <h2 className="card__title" id="image-upload-title">Image Upload</h2>
      </div>

      {!preview ? (
        <div
          id="image-dropzone"
          className={`image-uploader__dropzone ${isDragOver ? 'image-uploader__dropzone--dragover' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          role="button"
          tabIndex="0"
          aria-label="Upload an image of the emergency"
          onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') fileInputRef.current?.click(); }}
        >
          <span className="image-uploader__dropzone-icon" aria-hidden="true">🖼️</span>
          <span className="image-uploader__dropzone-text">
            Drag &amp; drop an image or click to browse
          </span>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            style={{ display: 'none' }}
            onChange={(e) => handleFile(e.target.files[0])}
            aria-hidden="true"
          />
        </div>
      ) : (
        <div className="image-uploader__preview" role="region" aria-label="Image preview">
          <img src={preview} alt="Uploaded preview of the emergency" />
          <button 
            className="image-uploader__remove" 
            onClick={removeImage} 
            type="button"
            aria-label="Remove image"
          >
            ✕
          </button>
        </div>
      )}
    </section>
  );
}
