'use client';

import { useEffect } from 'react';
import styles from './confirmation-popup.module.css';

type Props = {
  isOpen: boolean;
  title: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
  variant?: 'danger' | 'warning' | 'info';
  confirmText?: string;
  cancelText?: string;
};

export default function ConfirmationPopup({ isOpen, title, message, onConfirm, onCancel, variant = 'danger', confirmText = 'מחק', cancelText = 'ביטול' }: Props) {
  useEffect(() => {
    if (!isOpen) return;
    const handleEsc = (e: KeyboardEvent) => e.key === 'Escape' && onCancel();
    document.addEventListener('keydown', handleEsc);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', handleEsc);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onCancel]);

  if (!isOpen) return null;

  return (
    <div className={styles.overlay} onClick={onCancel}>
      <div className={`${styles.popup} ${styles[variant]}`} onClick={e => e.stopPropagation()}>
        <div className={styles.header}>
          <h3>{title}</h3>
          <button onClick={onCancel}>×</button>
        </div>
        <div className={styles.content}>
          <div className={styles.icon}>⚠️</div>
          <p>{message}</p>
        </div>
        <div className={styles.actions}>
          <button className={styles.cancel} onClick={onCancel}>{cancelText}</button>
          <button className={`${styles.confirm} ${styles[variant]}`} onClick={onConfirm}>{confirmText}</button>
        </div>
      </div>
    </div>
  );
}
