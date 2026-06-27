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
    <div className="lg:p-8">
      <div className="mx-auto flex w-full flex-col justify-center space-y-6 sm:w-[350px]">
        <Suspense fallback={<SignUpFallback />}>
          <SignUp2 />
        </Suspense>
      </div>
    </div>
  );
}
