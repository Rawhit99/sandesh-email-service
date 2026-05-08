// frontend/src/services/api.ts
import axios, { AxiosError } from 'axios';

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
  user_id?: number | null;
  default_attachments?: { filename: string; content_base64: string; mime_type?: string }[] | null;
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
  default_attachments?: { filename: string; content_base64: string; mime_type?: string }[] | null;
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

export interface NotificationCreate {
  template_id: string;
  email: string;
  cc_emails?: string[];
  payload: Record<string, any>;
  subject?: string;
  content?: string;
  subscriber_external_id?: string;
  channels?: string[];
  from_email?: string;
  sender_name?: string;
  attachments?: { filename: string; content_base64: string; mime_type?: string }[];
}

/** Same body as POST /api/notifications (create + send). */
export type EmailRequest = NotificationCreate;

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
  execution_run_id?: string | null;
  subscriber_external_id?: string | null;
  seen_at?: string | null;
  user_id?: number | null;
}

export interface Subscriber {
  id: number;
  user_id?: number | null;
  subscriber_id: string;
  email: string;
  data?: Record<string, any> | null;
  channels?: string[] | null;
  is_active: boolean;
  created_at: string;
}

export interface SubscriberCreateRequest {
  subscriber_id: string;
  email: string;
  data?: Record<string, any>;
  channels?: string[];
}

export interface SubscriberUpdateRequest {
  email?: string;
  data?: Record<string, any>;
  channels?: string[];
  is_active?: boolean;
}

export interface IntegrationStatus {
  slack_incoming_webhook: boolean;
  ms_teams_incoming_webhook: boolean;
  firebase: boolean;
  sns: boolean;
  twilio_whatsapp: boolean;
  redis_queue: boolean;
  subscriber_required: boolean;
  email_ses: boolean;
  email_smtp: boolean;
}

export interface IntegrationMe {
  slack_user_configured: boolean;
  slack_user_hint: string | null;
  teams_user_configured: boolean;
  teams_user_hint: string | null;
  environment: IntegrationStatus;
  email_delivery?: Record<string, unknown> | null;
}

export interface PlatformOrganization {
  id: number;
  name: string;
  org_slug: string | null;
  service_username: string | null;
  has_tenant_account: boolean;
}

export interface IntegrationCredential {
  id: number;
  channel: string;
  name: string;
  config: Record<string, any>;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface OrgTemplateSetting {
  template_id:   string;
  template_name: string;
  subject:       string;
  is_active:     boolean;
  /** false = platform admin has disabled this template for the org */
  is_enabled:    boolean;
}

/** Matches backend UserResponse (auth login/me). */
export interface AuthUser {
  id: number;
  username: string;
  organization_id?: number | null;
  organization_name?: string | null;
  organization_role?: string | null;
  is_platform_admin: boolean;
  is_active: boolean;
  created_at: string;
}

export interface IntegrationMeUpdateRequest {
  slack_webhook_url?: string;
  teams_webhook_url?: string;
  firebase_credentials_path?: string;
  sns_push_topic_arn?: string;
  sns_access_key_id?: string;
  sns_secret_access_key?: string;
  sns_session_token?: string;
  sns_region?: string;
  twilio_account_sid?: string;
  twilio_auth_token?: string;
  twilio_whatsapp_from?: string;
  redis_url?: string;
  email_delivery?: Record<string, unknown>;
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

  private resolveBaseUrl(): string {
    if (typeof window === 'undefined') {
      return this.baseUrl;
    }
    const runtimeApiUrl = (window as Window & { __ENV__?: { REACT_APP_API_URL?: string } })
      .__ENV__?.REACT_APP_API_URL;
    return runtimeApiUrl || this.baseUrl;
  }

  // Create axios instance with default headers
  private createAxiosInstance() {
    const token = typeof localStorage !== 'undefined' ? localStorage.getItem('token') : null;
    const bearer = token || this.apiKey;
    const orgId =
      typeof localStorage !== 'undefined' ? localStorage.getItem('sandesh-org-id') : null;
    return axios.create({
      baseURL: this.resolveBaseUrl(),
      headers: {
        'Content-Type': 'application/json',
        ...(bearer ? { Authorization: `Bearer ${bearer}` } : {}),
        ...(orgId && orgId.trim() ? { 'X-Sandesh-Organization-Id': orgId.trim() } : {}),
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

  async sendEmail(request: EmailRequest): Promise<Notification> {
    try {
      const axiosInstance = this.createAxiosInstance();
      const response = await axiosInstance.post<Notification>('/api/notifications', request);
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
      await axiosInstance.post(`/api/v1/notifications/${notificationId}/retry`);
    } catch (error) {
      this.handleError(error);
    }
  }

  async resendNotification(notificationId: number): Promise<void> {
    try {
      const axiosInstance = this.createAxiosInstance();
      await axiosInstance.post(`/api/v1/notifications/${notificationId}/resend`);
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

  async listSubscribers(): Promise<Subscriber[]> {
    try {
      const axiosInstance = this.createAxiosInstance();
      const response = await axiosInstance.get<Subscriber[]>('/api/v1/subscribers');
      return response.data;
    } catch (error) {
      this.handleError(error);
    }
  }

  async createSubscriber(body: SubscriberCreateRequest): Promise<Subscriber> {
    try {
      const axiosInstance = this.createAxiosInstance();
      const response = await axiosInstance.post<Subscriber>('/api/v1/subscribers', body);
      return response.data;
    } catch (error) {
      this.handleError(error);
    }
  }

  async deactivateSubscriber(subscriberId: string): Promise<Subscriber> {
    try {
      const axiosInstance = this.createAxiosInstance();
      const response = await axiosInstance.patch<Subscriber>(
        `/api/v1/subscribers/${encodeURIComponent(subscriberId)}/deactivate`
      );
      return response.data;
    } catch (error) {
      this.handleError(error);
    }
  }

  async updateSubscriber(subscriberId: string, body: SubscriberUpdateRequest): Promise<Subscriber> {
    try {
      const axiosInstance = this.createAxiosInstance();
      const response = await axiosInstance.patch<Subscriber>(
        `/api/v1/subscribers/${encodeURIComponent(subscriberId)}`,
        body
      );
      return response.data;
    } catch (error) {
      this.handleError(error);
    }
  }

  async getIntegrationStatus(): Promise<IntegrationStatus> {
    try {
      const axiosInstance = this.createAxiosInstance();
      const response = await axiosInstance.get<IntegrationStatus>('/api/v1/integrations/status');
      return response.data;
    } catch (error) {
      this.handleError(error);
    }
  }

  async getIntegrationMe(): Promise<IntegrationMe> {
    try {
      const axiosInstance = this.createAxiosInstance();
      const response = await axiosInstance.get<IntegrationMe>('/api/v1/integrations/me');
      return response.data;
    } catch (error) {
      this.handleError(error);
    }
  }

  async updateIntegrationMe(body: IntegrationMeUpdateRequest): Promise<IntegrationMe> {
    try {
      const axiosInstance = this.createAxiosInstance();
      const response = await axiosInstance.put<IntegrationMe>('/api/v1/integrations/me', body);
      return response.data;
    } catch (error) {
      this.handleError(error);
    }
  }

  async getAuthMe(): Promise<AuthUser> {
    try {
      const axiosInstance = this.createAxiosInstance();
      const response = await axiosInstance.get<AuthUser>('/api/v1/auth/me');
      return response.data;
    } catch (error) {
      this.handleError(error);
    }
  }

  async listPlatformOrganizations(): Promise<PlatformOrganization[]> {
    try {
      const axiosInstance = this.createAxiosInstance();
      const response = await axiosInstance.get<PlatformOrganization[]>('/api/v1/platform/organizations');
      return response.data;
    } catch (error) {
      this.handleError(error);
    }
  }

  async createPlatformOrganization(body: { name: string; org_slug?: string }): Promise<PlatformOrganization> {
    try {
      const axiosInstance = this.createAxiosInstance();
      const response = await axiosInstance.post<PlatformOrganization>('/api/v1/platform/organizations', body);
      return response.data;
    } catch (error) {
      this.handleError(error);
    }
  }

  async updatePlatformOrganization(id: number, body: { name?: string; org_slug?: string }): Promise<PlatformOrganization> {
    try {
      const axiosInstance = this.createAxiosInstance();
      const response = await axiosInstance.put<PlatformOrganization>(`/api/v1/platform/organizations/${id}`, body);
      return response.data;
    } catch (error) {
      this.handleError(error);
    }
  }

  // ── Integration Credentials ──────────────────────────────────────────────

  async listCredentials(channel?: string): Promise<IntegrationCredential[]> {
    try {
      const axiosInstance = this.createAxiosInstance();
      const params = channel ? { channel } : {};
      const response = await axiosInstance.get<IntegrationCredential[]>('/api/v1/credentials', { params });
      return response.data;
    } catch (error) {
      this.handleError(error);
    }
  }

  async createCredential(body: { channel: string; name: string; config: Record<string, any>; is_default?: boolean }): Promise<IntegrationCredential> {
    try {
      const axiosInstance = this.createAxiosInstance();
      const response = await axiosInstance.post<IntegrationCredential>('/api/v1/credentials', body);
      return response.data;
    } catch (error) {
      this.handleError(error);
    }
  }

  async updateCredential(id: number, body: { name?: string; config?: Record<string, any>; is_default?: boolean }): Promise<IntegrationCredential> {
    try {
      const axiosInstance = this.createAxiosInstance();
      const response = await axiosInstance.put<IntegrationCredential>(`/api/v1/credentials/${id}`, body);
      return response.data;
    } catch (error) {
      this.handleError(error);
    }
  }

  async setDefaultCredential(id: number): Promise<IntegrationCredential> {
    try {
      const axiosInstance = this.createAxiosInstance();
      const response = await axiosInstance.patch<IntegrationCredential>(`/api/v1/credentials/${id}/set-default`);
      return response.data;
    } catch (error) {
      this.handleError(error);
    }
  }

  async deleteCredential(id: number): Promise<void> {
    try {
      const axiosInstance = this.createAxiosInstance();
      await axiosInstance.delete(`/api/v1/credentials/${id}`);
    } catch (error) {
      this.handleError(error);
    }
  }

  // ── Org Template Scope ───────────────────────────────────────────────────

  async listOrgTemplates(orgId: number): Promise<OrgTemplateSetting[]> {
    try {
      const axiosInstance = this.createAxiosInstance();
      const response = await axiosInstance.get<OrgTemplateSetting[]>(
        `/api/v1/platform/organizations/${orgId}/templates`,
      );
      return response.data;
    } catch (error) {
      this.handleError(error);
    }
  }

  async updateOrgTemplateSetting(orgId: number, templateId: string, isEnabled: boolean): Promise<void> {
    try {
      const axiosInstance = this.createAxiosInstance();
      await axiosInstance.put(
        `/api/v1/platform/organizations/${orgId}/templates/${encodeURIComponent(templateId)}`,
        { is_enabled: isEnabled },
      );
    } catch (error) {
      this.handleError(error);
    }
  }

  async bulkUpdateOrgTemplates(orgId: number, isEnabled: boolean, templateIds?: string[]): Promise<void> {
    try {
      const axiosInstance = this.createAxiosInstance();
      await axiosInstance.post(
        `/api/v1/platform/organizations/${orgId}/templates/bulk`,
        { is_enabled: isEnabled, template_ids: templateIds ?? null },
      );
    } catch (error) {
      this.handleError(error);
    }
  }

  async markNotificationSeen(notificationId: number): Promise<void> {
    try {
      const axiosInstance = this.createAxiosInstance();
      await axiosInstance.patch(`/api/v1/notifications/${notificationId}/seen`);
    } catch (error) {
      this.handleError(error);
    }
  }

  async markNotificationUnseen(notificationId: number): Promise<void> {
    try {
      const axiosInstance = this.createAxiosInstance();
      await axiosInstance.patch(`/api/v1/notifications/${notificationId}/unseen`);
    } catch (error) {
      this.handleError(error);
    }
  }

  async triggerEvent(
    body: NotificationCreate & { workflow_name?: string }
  ): Promise<Notification> {
    try {
      const axiosInstance = this.createAxiosInstance();
      const response = await axiosInstance.post<Notification>('/api/v1/events/trigger', body);
      return response.data;
    } catch (error) {
      this.handleError(error);
    }
  }
}

const apiService = new ApiService();
export default apiService;