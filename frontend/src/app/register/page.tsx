"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardFooter,
} from "@/components/ui/card";

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    username: "",
    email: "",
    first_name: "",
    last_name: "",
    password: "",
    password_confirm: "",
  });
  const [errors, setErrors] = useState<Record<string, string[]>>({});
  const [generalError, setGeneralError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    setGeneralError("");
    setIsLoading(true);

    try {
      await api.post("/auth/register/", form);
      router.push("/login?registered=1");
    } catch (err: unknown) {
      if (
        err &&
        typeof err === "object" &&
        "response" in err &&
        (err as { response?: { data?: unknown } }).response?.data
      ) {
        const data = (err as { response: { data: Record<string, string[]> } })
          .response.data;
        if (typeof data === "object" && !Array.isArray(data)) {
          setErrors(data);
        } else {
          setGeneralError("Registration failed. Please try again.");
        }
      } else {
        setGeneralError("Registration failed. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const fieldError = (field: string) =>
    errors[field]?.length ? errors[field].join(" ") : null;

  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-b from-background to-secondary p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1 text-center">
          <CardTitle className="text-2xl font-bold">Create Account</CardTitle>
          <p className="text-sm text-muted-foreground">
            Register for AI Deal Manager
          </p>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            {generalError && (
              <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                {generalError}
              </div>
            )}
            {errors.non_field_errors && (
              <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                {errors.non_field_errors.join(" ")}
              </div>
            )}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label
                  htmlFor="first_name"
                  className="text-sm font-medium leading-none"
                >
                  First Name
                </label>
                <Input
                  id="first_name"
                  name="first_name"
                  type="text"
                  placeholder="John"
                  value={form.first_name}
                  onChange={handleChange}
                  autoComplete="given-name"
                />
                {fieldError("first_name") && (
                  <p className="text-xs text-destructive">
                    {fieldError("first_name")}
                  </p>
                )}
              </div>
              <div className="space-y-2">
                <label
                  htmlFor="last_name"
                  className="text-sm font-medium leading-none"
                >
                  Last Name
                </label>
                <Input
                  id="last_name"
                  name="last_name"
                  type="text"
                  placeholder="Doe"
                  value={form.last_name}
                  onChange={handleChange}
                  autoComplete="family-name"
                />
                {fieldError("last_name") && (
                  <p className="text-xs text-destructive">
                    {fieldError("last_name")}
                  </p>
                )}
              </div>
            </div>
            <div className="space-y-2">
              <label
                htmlFor="username"
                className="text-sm font-medium leading-none"
              >
                Username
              </label>
              <Input
                id="username"
                name="username"
                type="text"
                placeholder="johndoe"
                value={form.username}
                onChange={handleChange}
                required
                autoComplete="username"
              />
              {fieldError("username") && (
                <p className="text-xs text-destructive">
                  {fieldError("username")}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <label
                htmlFor="email"
                className="text-sm font-medium leading-none"
              >
                Email
              </label>
              <Input
                id="email"
                name="email"
                type="email"
                placeholder="john@example.com"
                value={form.email}
                onChange={handleChange}
                required
                autoComplete="email"
              />
              {fieldError("email") && (
                <p className="text-xs text-destructive">
                  {fieldError("email")}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <label
                htmlFor="password"
                className="text-sm font-medium leading-none"
              >
                Password
              </label>
              <Input
                id="password"
                name="password"
                type="password"
                placeholder="Min. 10 characters"
                value={form.password}
                onChange={handleChange}
                required
                autoComplete="new-password"
              />
              {fieldError("password") && (
                <p className="text-xs text-destructive">
                  {fieldError("password")}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <label
                htmlFor="password_confirm"
                className="text-sm font-medium leading-none"
              >
                Confirm Password
              </label>
              <Input
                id="password_confirm"
                name="password_confirm"
                type="password"
                placeholder="Repeat your password"
                value={form.password_confirm}
                onChange={handleChange}
                required
                autoComplete="new-password"
              />
              {fieldError("password_confirm") && (
                <p className="text-xs text-destructive">
                  {fieldError("password_confirm")}
                </p>
              )}
            </div>
          </CardContent>
          <CardFooter className="flex flex-col gap-4">
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? "Creating account..." : "Create Account"}
            </Button>
            <p className="text-sm text-muted-foreground">
              Already have an account?{" "}
              <Link href="/login" className="text-primary hover:underline">
                Sign in
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </main>
  );
}
