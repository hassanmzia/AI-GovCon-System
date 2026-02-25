import api from "@/lib/api";

export interface User {
  id: string | number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: "admin" | "executive" | "capture_manager" | "proposal_manager" | "pricing_manager" | "writer" | "reviewer" | "contracts_manager" | "viewer";
  is_mfa_enabled: boolean;
  is_active: boolean;
  date_joined: string;
}

export async function getUsers(): Promise<User[]> {
  const response = await api.get("/auth/users/");
  return Array.isArray(response.data) ? response.data : response.data.results || [];
}

export async function createUser(userData: {
  username: string;
  email: string;
  password: string;
  password_confirm: string;
  first_name?: string;
  last_name?: string;
  role?: string;
}): Promise<User> {
  const response = await api.post("/auth/users/", userData);
  return response.data;
}

export async function updateUser(id: string | number, userData: Partial<User>): Promise<User> {
  const response = await api.patch(`/auth/users/${id}/`, userData);
  return response.data;
}

export async function deleteUser(id: string | number): Promise<void> {
  await api.delete(`/auth/users/${id}/`);
}
