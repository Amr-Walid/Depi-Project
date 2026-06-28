import { SignUp2 } from "@/features/auth/components/sign-up-2";
import { Suspense } from "react";

function SignUpFallback() {
  return (
    <div className="flex flex-col items-center justify-center space-y-4">
      <p className="text-muted-foreground text-sm">Loading registration...</p>
    </div>
  );
}

export default function SignUpPage() {
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
      <div className="absolute inset-0 bg-black/65 backdrop-blur-xs" />

      {/* Central Glassmorphic Card (Soft rounded rectangle to fit multiple fields) */}
      <div className="relative z-10 w-full max-w-[460px] rounded-[40px] border border-white/10 bg-black/35 backdrop-blur-xl flex flex-col justify-center shadow-2xl shadow-cyan-500/5 p-8 sm:p-10">
        <Suspense fallback={<SignUpFallback />}>
          <SignUp2 />
        </Suspense>
      </div>
    </div>
  );
}
