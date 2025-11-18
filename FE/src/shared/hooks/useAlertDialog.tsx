import { useState } from 'react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/shared/components/ui/alert-dialog';

interface AlertDialogOptions {
  title?: string;
  description: string;
  confirmText?: string;
  onConfirm?: () => void;
}

export const useAlertDialog = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [options, setOptions] = useState<AlertDialogOptions>({
    title: '알림',
    description: '',
    confirmText: '확인',
  });

  const showAlert = (opts: AlertDialogOptions) => {
    setOptions({
      title: opts.title || '알림',
      description: opts.description,
      confirmText: opts.confirmText || '확인',
      onConfirm: opts.onConfirm,
    });
    setIsOpen(true);
  };

  const handleConfirm = () => {
    setIsOpen(false);
    options.onConfirm?.();
  };

  const AlertDialogComponent = () => (
    <AlertDialog open={isOpen} onOpenChange={setIsOpen}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle className="text-2xl">{options.title}</AlertDialogTitle>
          <AlertDialogDescription className="text-lg whitespace-pre-line">
            {options.description}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogAction 
            onClick={handleConfirm}
            className="text-lg px-6 py-4"
          >
            {options.confirmText}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );

  return {
    showAlert,
    AlertDialog: AlertDialogComponent,
  };
};

