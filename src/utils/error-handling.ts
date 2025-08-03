/**
 * Utility functions for standardized error handling across the application
 */

/**
 * Standard error types used throughout the application
 */
export type AppErrorType = 'api' | 'network' | 'validation' | 'streaming' | 'unknown';

/**
 * Standardized error structure
 */
export interface AppError {
  type: AppErrorType;
  message: string;
  retryable: boolean;
  code?: string;
}

/**
 * Creates a standardized error object
 */
export const createAppError = (
  type: AppErrorType, 
  message: string, 
  retryable: boolean = false,
  code?: string
): AppError => ({
  type,
  message,
  retryable,
  code
});

/**
 * Converts unknown errors to standardized format
 */
export const normalizeError = (error: unknown): AppError => {
  if (error instanceof Error) {
    return createAppError('unknown', error.message, false);
  }
  
  if (typeof error === 'string') {
    return createAppError('unknown', error, false);
  }
  
  return createAppError('unknown', 'An unexpected error occurred', false);
};

/**
 * Standard error messages in Hebrew for consistent UX
 */
export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'שגיאת רשת. אנא בדוק את החיבור לאינטרנט',
  API_UNAVAILABLE: 'שירות הבינה המלאכותית אינו זמין כרגע. אנא נסה שוב מאוחר יותר',
  INVALID_INPUT: 'קלט לא תקין. אנא בדוק את הנתונים שהוזנו',
  SESSION_EXPIRED: 'ההפעלה פגה. אנא רענן את הדף',
  UNKNOWN_ERROR: 'שגיאה לא צפויה. אנא נסה שוב',
  STREAMING_INTERRUPTED: 'הזרמת התגובה נקטעה. אנא נסה שוב'
} as const;

/**
 * Determines if an error should show a retry button
 */
export const isRetryableError = (error: AppError): boolean => {
  return error.retryable || error.type === 'network' || error.type === 'api';
};

/**
 * Gets user-friendly error message for display
 */
export const getErrorDisplayMessage = (error: AppError): string => {
  switch (error.type) {
    case 'network':
      return ERROR_MESSAGES.NETWORK_ERROR;
    case 'api':
      return error.message || ERROR_MESSAGES.API_UNAVAILABLE;
    case 'validation':
      return error.message || ERROR_MESSAGES.INVALID_INPUT;
    case 'streaming':
      return error.message || ERROR_MESSAGES.STREAMING_INTERRUPTED;
    default:
      return error.message || ERROR_MESSAGES.UNKNOWN_ERROR;
  }
}; 