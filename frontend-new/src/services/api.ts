// frontend/src/services/api.ts
import axios, { AxiosError } from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

// Add API key - you can set this in environment variables or use a default
const API_KEY = process.env.REACT_APP_API_KEY || '';

interface ErrorResponse {
  detail: string;
}

// Interfaces
export interface EmailTemplate {
  template_id: string;
  name: string;
  subject: string;
  content: string;
  variables: Record<string, string>;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface TemplateCreate {
  template_id: string;
  name: string;
  subject: string;
  content: string;
  variables: Record<string, string>;
  is_active: boolean;
}

export interface TemplateCreateRequest {
  template_id: string;
  name: string;
  subject: string;
  content: string;
  variables: Record<string, string>;
  is_active: boolean;
}

export interface TemplateFormData {
  template_id: string;
  name: string;
  subject: string;
  content: string;
  variables: Record<string, string>; // For form editing with key-value pairs
  is_active: boolean;
}

export interface TemplateUpdate {
  name?: string;
  subject?: string;
  content?: string;
  variables?: Record<string, string>;
  is_active?: boolean;
}

export interface TemplateValidationRequest {
  template_id?: string;
  name: string;
  subject: string;
  content: string;
  variables?: Record<string, string>;
  is_active?: boolean;
}

export interface TemplateValidationResponse {
  valid: boolean;
  variables?: string[];
  error?: string;
}

export interface EmailRequest {
  template_id: string;
  email: string;
  cc_emails?: string[];
  payload: Record<string, any>;
}

export interface NotificationCreate {
  template_id: string;
  email: string;
  cc_emails?: string[];
  payload: Record<string, any>;
  subject?: string;
  content?: string;
}

export interface Notification {
  id: number;
  template_id: string;
  email: string;
  payload: Record<string, any>;
  status: string;
  error_message?: string;
  executed_at: string;
  created_at: string;
  updated_at: string;
}

export interface NotificationFilters {
  status?: string;
  template_id?: string;
  email?: string;
  start_date?: string;
  end_date?: string;
}

export interface Stats {
  total_notifications: number;
  total_templates: number;
  notifications_24h: number;
  success_rate: number;
  status_counts: Record<string, number>;
  success_count: number;
  failed_count: number;
  pending_count: number;
  recent_notifications: NotificationSummary[];
  ses_quota?: SESStatus;
}

export interface NotificationSummary {
  id: number;
  template_id: string;
  email: string;
  status: string;
  created_at: string;
  executed_at?: string;
}

export interface SESStatus {
  max_24_hour: number;
  max_send_rate: number;
  sent_last_24_hours: number;
  send_data_points: any[];
}

export interface SESSettings {
  aws_access_key_id: string;
  aws_secret_access_key: string;
  aws_region: string;
  ses_sender_email: string;
  ses_configuration_set?: string;
}

export interface EmailResponse {
  message_id: string;
  status: string;
}

export interface Template {
  id?: number;
  template_id: string;
  name: string;
  subject: string;
  content: string;
  variables: Record<string, string>;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface TemplatePreviewResult {
  content: string;
}

export const convertFormDataToCreateRequest = (formData: TemplateFormData): TemplateCreateRequest => ({
  template_id: formData.template_id,
  name: formData.name,
  subject: formData.subject,
  content: formData.content,
  variables: formData.variables, // No conversion needed
  is_active: formData.is_active
});

export const convertTemplateToFormData = (template: EmailTemplate): TemplateFormData => ({
  template_id: template.template_id,
  name: template.name,
  subject: template.subject,
  content: template.content,
  variables: template.variables,
  is_active: template.is_active
});

class ApiService {
  private baseUrl: string;
  private apiKey: string;

  constructor() {
    this.baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    this.apiKey = API_KEY;
  }

  // Create axios instance with default headers
  private createAxiosInstance() {
    return axios.create({
      baseURL: this.baseUrl,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`,
      },
    });
  }

  private handleError(error: unknown): never {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError<ErrorResponse>;
      if (axiosError.response?.data?.detail) {
        throw new Error(axiosError.response.data.detail);
      }
      if (axiosError.response?.status === 403) {
        throw new Error('Access denied. Please check your API key.');
      }
      if (axiosError.response?.status === 404) {
        throw new Error('Resource not found');
      }
      if (axiosError.response?.status === 400) {
        throw new Error('Invalid request data');
      }
      if (axiosError.response?.status === 500) {
        throw new Error('Internal server error');
      }
      throw new Error(axiosError.message);
    }
    throw error;
  }

  async getTemplates(): Promise<EmailTemplate[]> {
    try {
      const axiosInstance = this.createAxiosInstance();
      const response = await axiosInstance.get<EmailTemplate[]>('/api/v1/templates');
      return response.data;
    } catch (error) {
      this.handleError(error);
    }
  }

  async getTemplate(templateId: string): Promise<EmailTemplate> {
    try {
      const axiosInstance = this.createAxiosInstance();
      const response = await axiosInstance.get<EmailTemplate>(`/api/v1/templates/${templateId}`);
      return response.data;
    } catch (error) {
      this.handleError(error);
    }
  }

  async validateTemplate(template: Omit<TemplateValidationRequest, 'template_id'> & { template_id?: string }): Promise<TemplateValidationResponse> {
    try {
      const axiosInstance = this.createAxiosInstance();
      const response = await axiosInstance.post<TemplateValidationResponse>('/api/v1/templates/validate', template);
      return response.data;
    } catch (error) {
      this.handleError(error);
    }
  }

  async addTemplate(template: TemplateCreateRequest): Promise<EmailTemplate> {
    try {
      const axiosInstance = this.createAxiosInstance();
      const response = await axiosInstance.post<EmailTemplate>('/api/v1/templates', template);
      return response.data;
    } catch (error) {
      this.handleError(error);
    }
  }

  async updateTemplate(templateId: string, template: TemplateCreateRequest): Promise<EmailTemplate> {
    try {
      const axiosInstance = this.createAxiosInstance();
      
      // Convert boolean is_active to string if needed
      const updateData = {
        ...template,
        is_active: template.is_active ? 'true' : 'false'
      };
      
      const response = await axiosInstance.put<EmailTemplate>(`/api/v1/templates/${templateId}`, updateData);
      return response.data;
    } catch (error) {
      this.handleError(error);
    }
  }

  async deleteTemplate(templateId: string): Promise<void> {
    try {
      const axiosInstance = this.createAxiosInstance();
      await axiosInstance.delete(`/api/v1/templates/${templateId}`);
    } catch (error) {
      this.handleError(error);
    }
  }

  async previewTemplate(content: string, variables: Record<string, any>): Promise<string> {
    try {
      const axiosInstance = this.createAxiosInstance();
      const response = await axiosInstance.post<TemplatePreviewResult>('/api/v1/templates/preview', { content, variables });
      return response.data.content;
    } catch (error) {
      this.handleError(error);
    }
  }

  async sendEmail(request: EmailRequest): Promise<EmailResponse> {
    try {
      const axiosInstance = this.createAxiosInstance();
      const response = await axiosInstance.post<EmailResponse>('/api/notifications', request);
      return response.data;
    } catch (error) {
      this.handleError(error);
    }
  }

  async createNotification(notification: NotificationCreate): Promise<void> {
    try {
      const axiosInstance = this.createAxiosInstance();
      await axiosInstance.post('/api/v1/notifications', notification);
    } catch (error) {
      this.handleError(error);
    }
  }

  async getStats(): Promise<Stats> {
    try {
      const axiosInstance = this.createAxiosInstance();
      const response = await axiosInstance.get<Stats>('/api/v1/stats');
      return response.data;
    } catch (error) {
      this.handleError(error);
    }
  }

  async getSESQuota(): Promise<SESStatus> {
    try {
      const axiosInstance = this.createAxiosInstance();
      const response = await axiosInstance.get<SESStatus>('/api/v1/ses/quota');
      return response.data;
    } catch (error) {
      this.handleError(error);
    }
  }

  async getNotifications(filters?: NotificationFilters): Promise<Notification[]> {
    try {
      const axiosInstance = this.createAxiosInstance();
      const response = await axiosInstance.get<Notification[]>('/api/v1/notifications', { params: filters });
      return response.data;
    } catch (error) {
      this.handleError(error);
    }
  }

  async retryNotification(notificationId: number): Promise<void> {
    try {
      const axiosInstance = this.createAxiosInstance();
      await axiosInstance.post(`/notifications/${notificationId}/retry`);
    } catch (error) {
      this.handleError(error);
    }
  }

  async resendNotification(notificationId: number): Promise<void> {
    try {
      const axiosInstance = this.createAxiosInstance();
      await axiosInstance.post(`/notifications/${notificationId}/resend`);
    } catch (error) {
      this.handleError(error);
    }
  }

  async getVerifiedEmails(): Promise<string[]> {
    try {
      const axiosInstance = this.createAxiosInstance();
      const response = await axiosInstance.get<string[]>('/api/v1/verified-emails');
      return response.data;
    } catch (error) {
      this.handleError(error);
    }
  }

  async verifyEmail(email: string): Promise<void> {
    try {
      const axiosInstance = this.createAxiosInstance();
      await axiosInstance.post('/api/v1/verify-email', { email });
    } catch (error) {
      this.handleError(error);
    }
  }

  async deleteVerifiedEmail(email: string): Promise<void> {
    try {
      const axiosInstance = this.createAxiosInstance();
      await axiosInstance.delete(`/api/v1/verified-emails/${email}`);
    } catch (error) {
      this.handleError(error);
    }
  }

  async getSESSettings(): Promise<SESSettings> {
    try {
      const axiosInstance = this.createAxiosInstance();
      const response = await axiosInstance.get<SESSettings>('/api/v1/settings/ses');
      return response.data;
    } catch (error) {
      this.handleError(error);
    }
  }

  async updateSESSettings(settings: SESSettings): Promise<void> {
    try {
      const axiosInstance = this.createAxiosInstance();
      await axiosInstance.put('/api/v1/settings/ses', settings);
    } catch (error) {
      this.handleError(error);
    }
  }

  async testSESSettings(settings: SESSettings): Promise<void> {
    try {
      const axiosInstance = this.createAxiosInstance();
      await axiosInstance.post('/api/v1/settings/ses/test', settings);
    } catch (error) {
      this.handleError(error);
    }
  }

  async createTemplate(template: Partial<Template>): Promise<Template> {
    try {
      // Validate required fields exist
      if (!template.template_id || !template.name || !template.subject || !template.content) {
        throw new Error('Missing required fields: template_id, name, subject, and content are required');
      }

      const validationResult = await this.validateTemplate({
        content: template.content,
        variables: template.variables ?? {},
        subject: template.subject,
        name: template.name
      });
      
      if (!validationResult.valid) {
        throw new Error(validationResult.error || 'Invalid template');
      }

      const axiosInstance = this.createAxiosInstance();
      const response = await axiosInstance.post<Template>('/api/v1/templates', template);
      return response.data;
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Failed to create template');
    }
  }

  async getEmailSettings(): Promise<any> {
    try {
      const axiosInstance = this.createAxiosInstance();
      const response = await axiosInstance.get('/api/v1/settings/email');
      return response.data;
    } catch (error) {
      this.handleError(error);
    }
  }

  async updateEmailSettings(settings: any): Promise<any> {
    try {
      const axiosInstance = this.createAxiosInstance();
      const response = await axiosInstance.put('/api/v1/settings/email', settings);
      return response.data;
    } catch (error) {
      this.handleError(error);
    }
  }

  async testEmailSettings(settings: any): Promise<any> {
    try {
      const axiosInstance = this.createAxiosInstance();
      const response = await axiosInstance.post('/api/v1/settings/email/test', settings);
      return response.data;
    } catch (error) {
      this.handleError(error);
    }
  }
}

export default new ApiService();