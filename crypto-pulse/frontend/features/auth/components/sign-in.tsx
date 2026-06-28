"use client";

import { Button } from "@/components/ui/button";
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
import { Eye, EyeOff, User, Lock } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { blockDisallowedPasswordChars } from "../utils/password-validation";
import { SignInSchema, signInSchema } from "../utils/sign-in-schema";

export default function SignIn() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { login } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const form = useForm<SignInSchema>({
    resolver: zodResolver(signInSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });



  const onSubmit = async (data: SignInSchema) => {
    try {
      setIsLoading(true);
      await login(data.email, data.password);
      toast.success("Signed in successfully!");
      const callbackUrl = searchParams.get("callbackUrl") || "/dashboard";
      router.push(callbackUrl);
      router.refresh();
    } catch (error) {
      console.error("Sign in error:", error);
      toast.error(
        error instanceof Error
          ? error.message
          : "Failed to sign in. Please check your credentials.",
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div 
      className="relative flex min-h-screen w-full items-center justify-center p-4 bg-zinc-950"
      style={{
        backgroundImage: "url('/login-bg.png')",
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundRepeat: "no-repeat",
      }}
    >
      {/* Dark overlay with background blur */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-xs" />

      {/* Central Glassmorphic Circle Card */}
      <div className="relative z-10 w-full max-w-[490px] aspect-square rounded-full border-[3px] border-cyan-400/35 bg-zinc-950/20 backdrop-blur-md flex flex-col justify-center items-center shadow-[0_0_50px_rgba(6,182,212,0.2),inset_0_0_25px_rgba(6,182,212,0.15)] px-12 sm:px-16 py-8">
        {/* Form Container to prevent overflow and keep text styled */}
        <div className="w-full flex flex-col items-center justify-center space-y-4">
          <div className="flex flex-col items-center gap-1 text-center">
            {/* Logo */}
            <img 
              src="/logo.png" 
              alt="CryptoPulse Logo" 
              className="h-20 w-auto object-contain mb-1 drop-shadow-[0_0_12px_rgba(6,182,212,0.4)]" 
            />
            <h1 className="text-2xl font-black tracking-wider text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.15)]">CryptoPulse</h1>
            <p className="text-[10px] font-bold text-cyan-400/80 uppercase tracking-widest">
              Pro Analytics
            </p>
          </div>

          <div className="w-full space-y-4 pt-1">
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-3.5">
                <FormField
                  control={form.control}
                  name="email"
                  render={({ field }) => (
                    <FormItem className="space-y-1">
                      <FormControl>
                        <div className="relative">
                          <User className="absolute left-4.5 top-1/2 -translate-y-1/2 size-4 text-cyan-400/50" />
                          <Input
                            type="email"
                            placeholder="Username"
                            disabled={isLoading}
                            className="h-11 rounded-full bg-black/30 border border-white/10 text-white placeholder:text-zinc-500 pl-11 pr-4 focus:border-cyan-400/50 focus:ring-1 focus:ring-cyan-400/50 transition-all"
                            {...field}
                          />
                        </div>
                      </FormControl>
                      <FormMessage className="text-[10px]" />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="password"
                  render={({ field }) => (
                    <FormItem className="space-y-1">
                      <FormControl>
                        <div className="relative">
                          <Lock className="absolute left-4.5 top-1/2 -translate-y-1/2 size-4 text-cyan-400/50" />
                          <Input
                            type={showPassword ? "text" : "password"}
                            placeholder="Password"
                            disabled={isLoading}
                            className="h-11 rounded-full bg-black/30 border border-white/10 text-white placeholder:text-zinc-500 pl-11 pr-12 focus:border-cyan-400/50 focus:ring-1 focus:ring-cyan-400/50 transition-all"
                            onBeforeInput={blockDisallowedPasswordChars}
                            {...field}
                          />
                          <button
                            type="button"
                            onClick={() => setShowPassword(!showPassword)}
                            className="absolute right-4 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300 transition-colors"
                            tabIndex={-1}
                          >
                            {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                          </button>
                        </div>
                      </FormControl>
                      <FormMessage className="text-[10px]" />
                    </FormItem>
                  )}
                />



                <Button
                  className="h-11 w-full bg-gradient-to-r from-cyan-400 via-cyan-500 to-indigo-500 font-bold text-black rounded-full transition-all hover:brightness-110 active:scale-95 shadow-[0_0_20px_rgba(6,182,212,0.45)] uppercase tracking-widest text-[11px]"
                  type="submit"
                  disabled={isLoading}
                >
                  {isLoading ? "Signing in..." : "Login"}
                </Button>
              </form>
            </Form>

            <div className="text-center text-[11px] text-zinc-400">
              Don&apos;t have an account?{" "}
              <Link href="/sign-up" className="text-cyan-400 hover:underline transition-colors font-semibold">
                Create Account
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
