'use client';

import { createContext, useContext, useState, ReactNode } from 'react';
import ConfirmationPopup from '../components/confirmation-popup/confirmation-popup';

type PopupConfig = {
  title: string;
  message: string;
  onConfirm: () => void;
  variant?: 'danger' | 'warning' | 'info';
  confirmText?: string;
  cancelText?: string;
};

const PopupContext = createContext<((config: PopupConfig) => void) | null>(null);

export const usePopup = () => {
  const show = useContext(PopupContext);
  if (!show) throw new Error('usePopup must be used within PopupProvider');
  return { showConfirmation: show };
};

export const PopupProvider = ({ children }: { children: ReactNode }) => {
  const [config, setConfig] = useState<PopupConfig | null>(null);

  const show = (newConfig: PopupConfig) => setConfig(newConfig);
  const hide = () => setTimeout(() => setConfig(null), 300);

  return (
    <PopupContext.Provider value={show}>
      {children}
      {config && (
        <ConfirmationPopup
          isOpen={!!config}
          title={config.title}
          message={config.message}
          variant={config.variant}
          confirmText={config.confirmText}
          cancelText={config.cancelText}
          onConfirm={() => { config.onConfirm(); hide(); }}
          onCancel={hide}
        />
      )}
    </PopupContext.Provider>
  );
};
