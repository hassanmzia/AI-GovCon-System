"use client";

import { useEffect, useState } from "react";
import { useAuthStore } from "@/store/auth";
import { getUsers, createUser, updateUser, deleteUser, User } from "@/services/users";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2, Plus, Edit2, Trash2, Search, X } from "lucide-react";

const ROLES = [
  { value: "admin", label: "Admin" },
  { value: "executive", label: "Executive" },
  { value: "capture_manager", label: "Capture Manager" },
  { value: "proposal_manager", label: "Proposal Manager" },
  { value: "pricing_manager", label: "Pricing Manager" },
  { value: "writer", label: "Writer" },
  { value: "reviewer", label: "Reviewer" },
  { value: "contracts_manager", label: "Contracts Manager" },
  { value: "viewer", label: "Viewer" },
];

type FormMode = "create" | "edit";

interface FormData {
  username: string;
  email: string;
  password: string;
  password_confirm: string;
  first_name: string;
  last_name: string;
  role: User["role"];
  is_active: boolean;
}

const EMPTY_FORM: FormData = {
  username: "",
  email: "",
  password: "",
  password_confirm: "",
  first_name: "",
  last_name: "",
  role: "viewer",
  is_active: true,
};

export default function AdminUsersPage() {
  const user = useAuthStore((state) => state.user);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [formMode, setFormMode] = useState<FormMode>("create");
  const [showModal, setShowModal] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formLoading, setFormLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [formData, setFormData] = useState<FormData>(EMPTY_FORM);
  const [deletingId, setDeletingId] = useState<string | number | null>(null);

  useEffect(() => {
    if (user && user.role !== "admin") {
      setError("Access denied. Only admins can manage users.");
    }
  }, [user]);

  useEffect(() => {
    if (user?.role === "admin") {
      fetchUsers();
    }
  }, [user]);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const data = await getUsers();
      setUsers(data);
      setError(null);
    } catch (err) {
      console.error("Failed to fetch users:", err);
      setError("Failed to load users. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const filteredUsers = users.filter(
    (u) =>
      u.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
      u.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      `${u.first_name} ${u.last_name}`.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getRoleColor = (role: string) => {
    switch (role) {
      case "admin": return "bg-red-100 text-red-800";
      case "executive": return "bg-purple-100 text-purple-800";
      case "capture_manager": return "bg-blue-100 text-blue-800";
      case "proposal_manager": return "bg-green-100 text-green-800";
      case "viewer": return "bg-gray-100 text-gray-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  const handleOpenCreate = () => {
    setFormMode("create");
    setSelectedUser(null);
    setFormData(EMPTY_FORM);
    setFormError(null);
    setShowModal(true);
  };

  const handleOpenEdit = (u: User) => {
    setFormMode("edit");
    setSelectedUser(u);
    setFormData({
      username: u.username,
      email: u.email,
      password: "",
      password_confirm: "",
      first_name: u.first_name,
      last_name: u.last_name,
      role: u.role,
      is_active: u.is_active,
    });
    setFormError(null);
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setSelectedUser(null);
    setFormError(null);
  };

  const handleDelete = async (u: User) => {
    if (!confirm(`Delete user "${u.username}"? This cannot be undone.`)) return;
    setDeletingId(u.id);
    try {
      await deleteUser(u.id);
      setUsers((prev) => prev.filter((x) => x.id !== u.id));
    } catch (err: any) {
      const data = err?.response?.data;
      const message =
        typeof data === "object"
          ? Object.values(data).flat().join(" ")
          : data?.detail || err?.message || "Failed to delete user";
      alert(message);
    } finally {
      setDeletingId(null);
    }
  };

  const handleFormChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? (e.target as HTMLInputElement).checked : value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (formMode === "create") {
      if (!formData.username || !formData.email || !formData.password) {
        setFormError("Username, email, and password are required");
        return;
      }
      if (formData.password !== formData.password_confirm) {
        setFormError("Passwords do not match");
        return;
      }
      try {
        setFormLoading(true);
        const newUser = await createUser({
          username: formData.username,
          email: formData.email,
          password: formData.password,
          password_confirm: formData.password_confirm,
          first_name: formData.first_name,
          last_name: formData.last_name,
          role: formData.role,
        });
        setUsers([...users, newUser]);
        handleCloseModal();
      } catch (err: any) {
        const data = err?.response?.data;
        const message =
          typeof data === "object"
            ? Object.values(data).flat().join(" ")
            : data?.detail || err?.message || "Failed to create user";
        setFormError(message);
      } finally {
        setFormLoading(false);
      }
    } else {
      // Edit mode
      if (formData.password && formData.password !== formData.password_confirm) {
        setFormError("Passwords do not match");
        return;
      }
      try {
        setFormLoading(true);
        const payload: Record<string, any> = {
          username: formData.username,
          email: formData.email,
          first_name: formData.first_name,
          last_name: formData.last_name,
          role: formData.role,
          is_active: formData.is_active,
        };
        if (formData.password) {
          payload.password = formData.password;
        }
        const updated = await updateUser(selectedUser!.id, payload);
        setUsers(users.map((u) => (u.id === updated.id ? updated : u)));
        handleCloseModal();
      } catch (err: any) {
        const data = err?.response?.data;
        const message =
          typeof data === "object"
            ? Object.values(data).flat().join(" ")
            : data?.detail || err?.message || "Failed to update user";
        setFormError(message);
      } finally {
        setFormLoading(false);
      }
    }
  };

  if (error && !user) {
    return (
      <div className="p-6">
        <div className="p-4 bg-red-100 text-red-800 rounded">{error}</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">User Management</h1>
          <p className="text-muted-foreground">Manage user accounts and roles</p>
        </div>
        <Button onClick={handleOpenCreate}>
          <Plus className="mr-2 h-4 w-4" />
          Add User
        </Button>
      </div>

      {/* Search */}
      <Card>
        <CardContent className="pt-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search users by name, email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-2 border rounded-md bg-background"
            />
          </div>
        </CardContent>
      </Card>

      {/* Users Table */}
      <Card>
        <CardHeader>
          <CardTitle>Users ({filteredUsers.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              <span className="ml-3 text-muted-foreground">Loading users...</span>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center py-12">
              <p className="text-red-600 mb-4">{error}</p>
              <Button variant="outline" onClick={fetchUsers}>Retry</Button>
            </div>
          ) : filteredUsers.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12">
              <p className="text-muted-foreground">No users found.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left">
                    <th className="pb-3 pr-4 font-medium text-muted-foreground">Name</th>
                    <th className="pb-3 pr-4 font-medium text-muted-foreground">Email</th>
                    <th className="pb-3 pr-4 font-medium text-muted-foreground">Username</th>
                    <th className="pb-3 pr-4 font-medium text-muted-foreground">Role</th>
                    <th className="pb-3 pr-4 font-medium text-muted-foreground">Status</th>
                    <th className="pb-3 pr-4 font-medium text-muted-foreground">MFA</th>
                    <th className="pb-3 font-medium text-muted-foreground">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredUsers.map((u) => (
                    <tr key={u.id} className="border-b hover:bg-muted/50">
                      <td className="py-3 pr-4 font-medium">{u.first_name} {u.last_name}</td>
                      <td className="py-3 pr-4 text-muted-foreground">{u.email}</td>
                      <td className="py-3 pr-4 text-muted-foreground">{u.username}</td>
                      <td className="py-3 pr-4">
                        <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${getRoleColor(u.role)}`}>
                          {ROLES.find((r) => r.value === u.role)?.label || u.role}
                        </span>
                      </td>
                      <td className="py-3 pr-4">
                        <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${u.is_active ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>
                          {u.is_active ? "Active" : "Inactive"}
                        </span>
                      </td>
                      <td className="py-3 pr-4 text-muted-foreground">
                        {u.is_mfa_enabled ? "✓ Enabled" : "Disabled"}
                      </td>
                      <td className="py-3 flex gap-2">
                        <button
                          onClick={() => handleOpenEdit(u)}
                          className="p-1 hover:bg-muted rounded"
                          title="Edit user"
                        >
                          <Edit2 className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(u)}
                          disabled={deletingId === u.id}
                          className="p-1 hover:bg-muted rounded text-red-600 disabled:opacity-40"
                          title="Delete user"
                        >
                          {deletingId === u.id
                            ? <Loader2 className="h-4 w-4 animate-spin" />
                            : <Trash2 className="h-4 w-4" />}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create / Edit User Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md max-h-[90vh] overflow-y-auto">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>{formMode === "edit" ? "Edit User" : "Add New User"}</CardTitle>
              <button onClick={handleCloseModal} className="p-1 hover:bg-muted rounded">
                <X className="h-4 w-4" />
              </button>
            </CardHeader>
            <CardContent>
              {formError && (
                <div className="mb-4 p-3 bg-red-100 text-red-800 rounded text-sm">
                  {formError}
                </div>
              )}
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Username</label>
                  <input
                    type="text"
                    name="username"
                    value={formData.username}
                    onChange={handleFormChange}
                    className="w-full px-3 py-2 border rounded-md bg-background"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Email</label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleFormChange}
                    className="w-full px-3 py-2 border rounded-md bg-background"
                    required
                  />
                </div>
                <div className="flex gap-3">
                  <div className="flex-1">
                    <label className="block text-sm font-medium mb-1">First Name</label>
                    <input
                      type="text"
                      name="first_name"
                      value={formData.first_name}
                      onChange={handleFormChange}
                      className="w-full px-3 py-2 border rounded-md bg-background"
                    />
                  </div>
                  <div className="flex-1">
                    <label className="block text-sm font-medium mb-1">Last Name</label>
                    <input
                      type="text"
                      name="last_name"
                      value={formData.last_name}
                      onChange={handleFormChange}
                      className="w-full px-3 py-2 border rounded-md bg-background"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Role</label>
                  <select
                    name="role"
                    value={formData.role}
                    onChange={handleFormChange}
                    className="w-full px-3 py-2 border rounded-md bg-background"
                  >
                    {ROLES.map((role) => (
                      <option key={role.value} value={role.value}>
                        {role.label}
                      </option>
                    ))}
                  </select>
                </div>
                {formMode === "edit" && (
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      id="is_active"
                      name="is_active"
                      checked={formData.is_active}
                      onChange={handleFormChange}
                      className="h-4 w-4 rounded border"
                    />
                    <label htmlFor="is_active" className="text-sm font-medium">
                      Active account
                    </label>
                  </div>
                )}
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Password{formMode === "edit" && <span className="text-muted-foreground font-normal"> (leave blank to keep unchanged)</span>}
                  </label>
                  <input
                    type="password"
                    name="password"
                    value={formData.password}
                    onChange={handleFormChange}
                    className="w-full px-3 py-2 border rounded-md bg-background"
                    required={formMode === "create"}
                    placeholder={formMode === "edit" ? "••••••••" : ""}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Confirm Password</label>
                  <input
                    type="password"
                    name="password_confirm"
                    value={formData.password_confirm}
                    onChange={handleFormChange}
                    className="w-full px-3 py-2 border rounded-md bg-background"
                    required={formMode === "create"}
                    placeholder={formMode === "edit" ? "••••••••" : ""}
                  />
                </div>
                <div className="flex gap-2 pt-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleCloseModal}
                    className="flex-1"
                    disabled={formLoading}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" className="flex-1" disabled={formLoading}>
                    {formLoading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        {formMode === "edit" ? "Saving..." : "Creating..."}
                      </>
                    ) : formMode === "edit" ? (
                      "Save Changes"
                    ) : (
                      "Create User"
                    )}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
