import api from "@/lib/api";

// ── Types ────────────────────────────────────────────────────

export interface SAMContact {
  id: string;
  registration: string;
  role: string;
  role_display: string;
  name: string;
  title: string;
  email: string;
  phone: string;
  created_at: string;
  updated_at: string;
}

export interface SAMRegistration {
  id: string;
  owner: string;
  uei_number: string;
  cage_code: string;
  tracking_number: string;
  ein_number: string;
  legal_business_name: string;
  physical_address: string;
  entity_type: string;
  status: string;
  status_display: string;
  registration_date: string | null;
  expiration_date: string | null;
  submitted_date: string | null;
  steps_completed: boolean[];
  steps_progress: { completed: number; total: number };
  validation_items: Record<string, boolean>;
  validation_progress: { checked: number; total: number };
  days_until_expiration: number | null;
  contacts: SAMContact[];
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface SAMRegistrationListItem {
  id: string;
  legal_business_name: string;
  uei_number: string;
  status: string;
  status_display: string;
  registration_date: string | null;
  expiration_date: string | null;
  steps_progress: { completed: number; total: number };
  created_at: string;
  updated_at: string;
}

export interface CreateSAMRegistrationPayload {
  legal_business_name?: string;
  uei_number?: string;
  cage_code?: string;
  tracking_number?: string;
  ein_number?: string;
  physical_address?: string;
  entity_type?: string;
  status?: string;
  registration_date?: string | null;
  expiration_date?: string | null;
  submitted_date?: string | null;
  steps_completed?: boolean[];
  validation_items?: Record<string, boolean>;
  notes?: string;
}

export interface CreateSAMContactPayload {
  registration: string;
  role: string;
  name: string;
  title?: string;
  email: string;
  phone?: string;
}

// ── Registration API ─────────────────────────────────────────

export async function getSAMRegistrations(): Promise<{
  results: SAMRegistrationListItem[];
  count: number;
}> {
  const response = await api.get("/sam-registration/registrations/");
  return response.data;
}

export async function getSAMRegistration(
  id: string
): Promise<SAMRegistration> {
  const response = await api.get(`/sam-registration/registrations/${id}/`);
  return response.data;
}

export async function createSAMRegistration(
  payload: CreateSAMRegistrationPayload
): Promise<SAMRegistration> {
  const response = await api.post(
    "/sam-registration/registrations/",
    payload
  );
  return response.data;
}

export async function updateSAMRegistration(
  id: string,
  payload: Partial<CreateSAMRegistrationPayload>
): Promise<SAMRegistration> {
  const response = await api.patch(
    `/sam-registration/registrations/${id}/`,
    payload
  );
  return response.data;
}

export async function updateSAMSteps(
  id: string,
  stepsCompleted: boolean[]
): Promise<SAMRegistration> {
  const response = await api.patch(
    `/sam-registration/registrations/${id}/update_steps/`,
    { steps_completed: stepsCompleted }
  );
  return response.data;
}

export async function updateSAMValidation(
  id: string,
  validationItems: Record<string, boolean>
): Promise<SAMRegistration> {
  const response = await api.patch(
    `/sam-registration/registrations/${id}/update_validation/`,
    { validation_items: validationItems }
  );
  return response.data;
}

export async function checkSAMExpiration(
  id: string
): Promise<{ warning: boolean; days_left?: number; message: string }> {
  const response = await api.post(
    `/sam-registration/registrations/${id}/check_expiration/`
  );
  return response.data;
}

// ── Contact API ──────────────────────────────────────────────

export async function getSAMContacts(
  registrationId?: string
): Promise<{ results: SAMContact[]; count: number }> {
  const params = registrationId
    ? { registration: registrationId }
    : undefined;
  const response = await api.get("/sam-registration/contacts/", { params });
  return response.data;
}

export async function createSAMContact(
  payload: CreateSAMContactPayload
): Promise<SAMContact> {
  const response = await api.post("/sam-registration/contacts/", payload);
  return response.data;
}

export async function updateSAMContact(
  id: string,
  payload: Partial<CreateSAMContactPayload>
): Promise<SAMContact> {
  const response = await api.patch(
    `/sam-registration/contacts/${id}/`,
    payload
  );
  return response.data;
}

export async function deleteSAMContact(id: string): Promise<void> {
  await api.delete(`/sam-registration/contacts/${id}/`);
}
