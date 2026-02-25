'use client';

import { useState, useEffect } from 'react';
import api from '@/lib/api';

interface UserData {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  is_mfa_enabled: boolean;
}

interface UserProfileData {
  id: string;
  user: UserData;
  title: string;
  department: string;
  phone: string;
  bio: string;
  avatar: string;
  skills: string[];
  clearances: string[];
  notification_preferences: Record<string, any>;
}

export default function ProfilePage() {
  const [profile, setProfile] = useState<UserProfileData | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [showMFASetup, setShowMFASetup] = useState(false);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Form states
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
  });

  const [profileData, setProfileData] = useState({
    title: '',
    department: '',
    phone: '',
    bio: '',
  });

  const [passwords, setPasswords] = useState({
    old_password: '',
    new_password: '',
    new_password_confirm: '',
  });

  useEffect(() => {
    fetchUserProfile();
  }, []);

  const fetchUserProfile = async () => {
    try {
      const response = await api.get('/auth/profile/');
      const data = response.data;
      setProfile(data);
      setFormData({
        first_name: data.user.first_name,
        last_name: data.user.last_name,
        email: data.user.email,
      });
      setProfileData({
        title: data.title || '',
        department: data.department || '',
        phone: data.phone || '',
        bio: data.bio || '',
      });
      if (data.avatar) {
        setAvatarPreview(data.avatar);
      }
    } catch (error) {
      console.error('Failed to fetch profile:', error);
      setMessage({ type: 'error', text: 'Failed to load profile' });
    } finally {
      setLoading(false);
    }
  };

  const showAlert = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 3000);
  };

  const handleProfileUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await api.patch('/auth/profile/', profileData);
      setProfile(response.data);
      setEditing(false);
      showAlert('success', 'Profile updated successfully!');
    } catch (error) {
      console.error('Failed to update profile:', error);
      showAlert('error', 'Failed to update profile');
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    if (passwords.new_password !== passwords.new_password_confirm) {
      showAlert('error', 'New passwords do not match');
      return;
    }

    try {
      await api.post('/auth/change-password/', {
        old_password: passwords.old_password,
        new_password: passwords.new_password,
      });
      setPasswords({
        old_password: '',
        new_password: '',
        new_password_confirm: '',
      });
      setShowPasswordForm(false);
      showAlert('success', 'Password changed successfully!');
    } catch (error: any) {
      console.error('Failed to change password:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to change password';
      showAlert('error', errorMessage);
    }
  };

  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file size (5MB)
    if (file.size > 5 * 1024 * 1024) {
      showAlert('error', 'File size must be less than 5MB');
      return;
    }

    // Preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setAvatarPreview(reader.result as string);
    };
    reader.readAsDataURL(file);

    // Upload
    const formData = new FormData();
    formData.append('avatar', file);

    try {
      const response = await api.patch('/auth/profile/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setProfile(response.data);
      showAlert('success', 'Profile picture uploaded successfully!');
    } catch (error) {
      console.error('Failed to upload avatar:', error);
      showAlert('error', 'Failed to upload profile picture');
    }
  };

  const handleMFAToggle = async () => {
    try {
      const endpoint = profile?.user.is_mfa_enabled
        ? '/auth/mfa/disable/'
        : '/auth/mfa/setup/';

      await api.post(endpoint);
      if (profile) {
        setProfile({
          ...profile,
          user: {
            ...profile.user,
            is_mfa_enabled: !profile.user.is_mfa_enabled,
          },
        });
      }
      showAlert('success', `MFA ${profile?.user.is_mfa_enabled ? 'disabled' : 'setup initiated'}`);
      setShowMFASetup(false);
    } catch (error: any) {
      console.error('Failed to update MFA:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to update MFA settings';
      showAlert('error', errorMessage);
    }
  };

  if (loading) {
    return <div className="p-6">Loading profile...</div>;
  }

  if (!profile) {
    return <div className="p-6 text-red-600">Failed to load profile</div>;
  }

  const user = profile.user;

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Profile</h1>

      {/* Messages */}
      {message && (
        <div
          className={`p-4 rounded ${
            message.type === 'success'
              ? 'bg-green-100 text-green-800'
              : 'bg-red-100 text-red-800'
          }`}
        >
          {message.text}
        </div>
      )}

      {/* Avatar Section */}
      <div className="p-6 border rounded-lg">
        <h2 className="text-xl font-semibold mb-4">Profile Picture</h2>
        <div className="flex items-center space-x-6">
          <div className="w-24 h-24 rounded-full bg-gray-200 flex items-center justify-center overflow-hidden">
            {avatarPreview ? (
              <img src={avatarPreview} alt="Profile" className="w-full h-full object-cover" />
            ) : (
              <div className="text-center">
                <div className="text-3xl font-bold">
                  {user.first_name.charAt(0).toUpperCase()}
                  {user.last_name.charAt(0).toUpperCase()}
                </div>
              </div>
            )}
          </div>
          <div>
            <label className="block mb-2">
              <input
                type="file"
                accept="image/*"
                onChange={handleAvatarUpload}
                className="hidden"
              />
              <span className="px-4 py-2 bg-blue-500 text-white rounded cursor-pointer hover:bg-blue-600">
                Upload Photo
              </span>
            </label>
            <p className="text-sm text-gray-600">JPG, PNG or GIF (max 5MB)</p>
          </div>
        </div>
      </div>

      {/* Profile Information Section */}
      <div className="p-6 border rounded-lg">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Profile Information</h2>
          <button
            onClick={() => setEditing(!editing)}
            className="px-3 py-1 text-sm bg-gray-200 rounded hover:bg-gray-300"
          >
            {editing ? 'Cancel' : 'Edit'}
          </button>
        </div>

        {editing ? (
          <form onSubmit={handleProfileUpdate} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">First Name</label>
                <input
                  type="text"
                  value={formData.first_name}
                  onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                  className="w-full px-3 py-2 border rounded"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Last Name</label>
                <input
                  type="text"
                  value={formData.last_name}
                  onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                  className="w-full px-3 py-2 border rounded"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Email</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-3 py-2 border rounded"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Title</label>
              <input
                type="text"
                value={profileData.title}
                onChange={(e) => setProfileData({ ...profileData, title: e.target.value })}
                className="w-full px-3 py-2 border rounded"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Department</label>
              <input
                type="text"
                value={profileData.department}
                onChange={(e) => setProfileData({ ...profileData, department: e.target.value })}
                className="w-full px-3 py-2 border rounded"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Phone</label>
              <input
                type="tel"
                value={profileData.phone}
                onChange={(e) => setProfileData({ ...profileData, phone: e.target.value })}
                className="w-full px-3 py-2 border rounded"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Bio</label>
              <textarea
                value={profileData.bio}
                onChange={(e) => setProfileData({ ...profileData, bio: e.target.value })}
                className="w-full px-3 py-2 border rounded h-24"
              />
            </div>

            <button
              type="submit"
              className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
            >
              Save Changes
            </button>
          </form>
        ) : (
          <div className="space-y-3">
            <p>
              <strong>Name:</strong> {formData.first_name} {formData.last_name}
            </p>
            <p>
              <strong>Email:</strong> {formData.email}
            </p>
            <p>
              <strong>Username:</strong> {user.username}
            </p>
            <p>
              <strong>Role:</strong> {user.role}
            </p>
            <p>
              <strong>Title:</strong> {profileData.title || 'Not set'}
            </p>
            <p>
              <strong>Department:</strong> {profileData.department || 'Not set'}
            </p>
            <p>
              <strong>Phone:</strong> {profileData.phone || 'Not set'}
            </p>
            <p>
              <strong>Bio:</strong> {profileData.bio || 'Not set'}
            </p>
          </div>
        )}
      </div>

      {/* Security Section */}
      <div className="p-6 border rounded-lg">
        <h2 className="text-xl font-semibold mb-4">Security Settings</h2>
        <div className="space-y-4">
          {/* Password Change */}
          <div className="pb-4 border-b">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="font-semibold">Password</h3>
                <p className="text-sm text-gray-600">
                  Change your password regularly for security
                </p>
              </div>
              <button
                onClick={() => setShowPasswordForm(!showPasswordForm)}
                className="px-3 py-1 text-sm bg-gray-200 rounded hover:bg-gray-300"
              >
                {showPasswordForm ? 'Cancel' : 'Change'}
              </button>
            </div>

            {showPasswordForm && (
              <form onSubmit={handlePasswordChange} className="mt-4 space-y-3">
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Current Password
                  </label>
                  <input
                    type="password"
                    value={passwords.old_password}
                    onChange={(e) =>
                      setPasswords({ ...passwords, old_password: e.target.value })
                    }
                    className="w-full px-3 py-2 border rounded"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">New Password</label>
                  <input
                    type="password"
                    value={passwords.new_password}
                    onChange={(e) =>
                      setPasswords({ ...passwords, new_password: e.target.value })
                    }
                    className="w-full px-3 py-2 border rounded"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Confirm New Password
                  </label>
                  <input
                    type="password"
                    value={passwords.new_password_confirm}
                    onChange={(e) =>
                      setPasswords({ ...passwords, new_password_confirm: e.target.value })
                    }
                    className="w-full px-3 py-2 border rounded"
                    required
                  />
                </div>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                >
                  Update Password
                </button>
              </form>
            )}
          </div>

          {/* MFA */}
          <div className="pb-4 border-b">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="font-semibold">Two-Factor Authentication</h3>
                <p className="text-sm text-gray-600">
                  {user.is_mfa_enabled
                    ? 'MFA is enabled'
                    : 'Add an extra layer of security'}
                </p>
              </div>
              <button
                onClick={() => setShowMFASetup(!showMFASetup)}
                className={`px-3 py-1 text-sm rounded ${
                  user.is_mfa_enabled
                    ? 'bg-red-200 hover:bg-red-300'
                    : 'bg-green-200 hover:bg-green-300'
                }`}
              >
                {user.is_mfa_enabled ? 'Disable' : 'Enable'}
              </button>
            </div>

            {showMFASetup && (
              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded">
                <p className="mb-4 text-sm">
                  {user.is_mfa_enabled
                    ? 'Disable two-factor authentication for this account.'
                    : 'We will send you a QR code to scan with an authenticator app like Google Authenticator or Authy.'}
                </p>
                <button
                  onClick={handleMFAToggle}
                  className={`px-4 py-2 rounded text-white ${
                    user.is_mfa_enabled
                      ? 'bg-red-500 hover:bg-red-600'
                      : 'bg-blue-500 hover:bg-blue-600'
                  }`}
                >
                  {user.is_mfa_enabled ? 'Disable MFA' : 'Start MFA Setup'}
                </button>
              </div>
            )}
          </div>

          {/* Session Info */}
          <div>
            <h3 className="font-semibold mb-2">Active Sessions</h3>
            <p className="text-sm text-gray-600">You are currently signed in</p>
          </div>
        </div>
      </div>
    </div>
  );
}
