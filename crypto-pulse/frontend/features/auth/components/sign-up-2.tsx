"use client";

import { PasswordRequirements } from "@/components/password-requirements";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/contexts/auth-context";
import { cn } from "@/lib/utils";
import { zodResolver } from "@hookform/resolvers/zod";
import { Eye, EyeOff, User, Lock, Mail } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { blockDisallowedPasswordChars } from "../utils/password-validation";
import { SignUp2Schema, signUp2Schema } from "../utils/sign-up-2-schema";

export function SignUp2({ className, ...props }: React.ComponentProps<"div">) {
  const { signup } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [isSocialLoading, setIsSocialLoading] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const form = useForm<SignUp2Schema>({
    resolver: zodResolver(signUp2Schema),
    defaultValues: {
      firstName: "",
      lastName: "",
      email: "",
      password: "",
      confirmPassword: "",
      terms: false,
    },
  });

  const handleSocialSignUp = async (provider: "google" | "github") => {
    try {
      setIsSocialLoading(provider);
      await new Promise((resolve) => setTimeout(resolve, 1500));
      toast.success(`Signed up with ${provider} successfully!`);
      window.location.href = "/dashboard";
    } catch {
      toast.error(`Failed to sign up with ${provider}. Please try again.`);
    } finally {
      setIsSocialLoading(null);
    }
  };

  const onSubmit = async (data: SignUp2Schema) => {
    try {
      setIsLoading(true);
      await signup(data.email, data.password);
      toast.success("Account created successfully!");
      window.location.href = "/dashboard";
    } catch (error) {
      console.error("Signup error:", error);
      toast.error(
        error instanceof Error
          ? error.message
          : "Failed to create account. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={cn("flex flex-col gap-5", className)} {...props}>
      <div className="flex flex-col items-center gap-1 text-center">
        {/* Logo */}
        <img 
          src="/logo.png" 
          alt="CryptoPulse Logo" 
          className="h-16 w-auto object-contain mb-1 drop-shadow-[0_0_12px_rgba(6,182,212,0.4)]" 
        />
        <h1 className="text-xl font-black tracking-wider text-white">Create Account</h1>
        <p className="text-[10px] text-cyan-400/80 uppercase tracking-wider">
          Join the Pro Analytics network
        </p>
      </div>

      <div className="grid gap-3">
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <FormField
                control={form.control}
                name="firstName"
                render={({ field }) => (
                  <FormItem className="space-y-0.5">
                    <FormControl>
                      <div className="relative">
                        <User className="absolute left-3.5 top-1/2 -translate-y-1/2 size-3.5 text-cyan-400/50" />
                        <Input
                          placeholder="First Name"
                          disabled={isLoading}
                          className="h-10 rounded-full bg-black/30 border border-white/10 text-white placeholder:text-zinc-500 pl-10 pr-3 focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 text-xs transition-all"
                          {...field}
                        />
                      </div>
                    </FormControl>
                    <FormMessage className="text-[9px]" />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="lastName"
                render={({ field }) => (
                  <FormItem className="space-y-0.5">
                    <FormControl>
                      <div className="relative">
                        <User className="absolute left-3.5 top-1/2 -translate-y-1/2 size-3.5 text-cyan-400/50" />
                        <Input
                          placeholder="Last Name"
                          disabled={isLoading}
                          className="h-10 rounded-full bg-black/30 border border-white/10 text-white placeholder:text-zinc-500 pl-10 pr-3 focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 text-xs transition-all"
                          {...field}
                        />
                      </div>
                    </FormControl>
                    <FormMessage className="text-[9px]" />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem className="space-y-0.5">
                  <FormControl>
                    <div className="relative">
                      <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 size-3.5 text-cyan-400/50" />
                      <Input
                        type="email"
                        placeholder="Email Address"
                        disabled={isLoading}
                        className="h-10 rounded-full bg-black/30 border border-white/10 text-white placeholder:text-zinc-500 pl-10 pr-3 focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 text-xs transition-all"
                        {...field}
                      />
                    </div>
                  </FormControl>
                  <FormMessage className="text-[9px]" />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem className="space-y-0.5">
                  <FormControl>
                    <div className="relative">
                      <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 size-3.5 text-cyan-400/50" />
                      <Input
                        type={showPassword ? "text" : "password"}
                        placeholder="Password"
                        disabled={isLoading}
                        className="h-10 rounded-full bg-black/30 border border-white/10 text-white placeholder:text-zinc-500 pl-10 pr-10 focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 text-xs transition-all"
                        onBeforeInput={blockDisallowedPasswordChars}
                        {...field}
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3.5 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300 transition-colors"
                      >
                        {showPassword ? <EyeOff className="size-3.5" /> : <Eye className="size-3.5" />}
                      </button>
                    </div>
                  </FormControl>
                  <PasswordRequirements password={field.value} />
                  <FormMessage className="text-[9px]" />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="confirmPassword"
              render={({ field }) => (
                <FormItem className="space-y-0.5">
                  <FormControl>
                    <div className="relative">
                      <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 size-3.5 text-cyan-400/50" />
                      <Input
                        type={showConfirmPassword ? "text" : "password"}
                        placeholder="Confirm Password"
                        disabled={isLoading}
                        className="h-10 rounded-full bg-black/30 border border-white/10 text-white placeholder:text-zinc-500 pl-10 pr-10 focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 text-xs transition-all"
                        onBeforeInput={blockDisallowedPasswordChars}
                        {...field}
                      />
                      <button
                        type="button"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        className="absolute right-3.5 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300 transition-colors"
                      >
                        {showConfirmPassword ? <EyeOff className="size-3.5" /> : <Eye className="size-3.5" />}
                      </button>
                    </div>
                  </FormControl>
                  <FormMessage className="text-[9px]" />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="terms"
              render={({ field }) => (
                <FormItem className="flex items-start gap-2 space-y-0 pt-1">
                  <FormControl>
                    <Checkbox
                      checked={field.value}
                      onCheckedChange={field.onChange}
                      disabled={isLoading}
                      className="mt-0.5 border-white/20 data-[state=checked]:bg-cyan-500 data-[state=checked]:text-black"
                    />
                  </FormControl>
                  <FormLabel className="text-[10px] font-normal text-zinc-400 cursor-pointer leading-tight">
                    I agree to the{" "}
                    <Link href="#" className="text-cyan-400 hover:underline">
                      Terms
                    </Link>{" "}
                    and{" "}
                    <Link href="#" className="text-cyan-400 hover:underline">
                      Privacy Policy
                    </Link>
                  </FormLabel>
                </FormItem>
              )}
            />

            <Button
              type="submit"
              className="h-10 w-full bg-gradient-to-r from-cyan-400 via-cyan-500 to-indigo-500 font-bold text-black rounded-full transition-all hover:brightness-110 active:scale-95 shadow-[0_0_20px_rgba(6,182,212,0.45)] uppercase tracking-widest text-[11px] mt-2"
              disabled={isLoading}
            >
              {isLoading ? "Creating..." : "Sign Up"}
            </Button>
          </form>
        </Form>
      </div>

      <div className="text-center text-[11px]">
        <span className="text-zinc-400">Already have an account? </span>
        <Link href="/sign-in" className="text-cyan-400 hover:underline font-semibold transition-colors">
          Sign In
        </Link>
      </div>
    </div>
  );
}
