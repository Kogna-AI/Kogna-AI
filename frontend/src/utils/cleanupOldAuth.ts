/**
 * Cleanup utility to remove old Supabase auth data from localStorage
 * Run this once on app startup to migrate existing users to the new auth system
 */

export function cleanupOldSupabaseAuth() {
  if (typeof window === "undefined") return;

  const keysToRemove = [
    "kogna-supabase-auth", // Old Supabase session
    "supabase.auth.token", // Alternative Supabase key pattern
    "sb-", // Any Supabase keys (they start with sb-)
    "token", // Old JWT token in localStorage
  ];

  // Remove exact matches
  keysToRemove.forEach((key) => {
    if (localStorage.getItem(key)) {
      console.log(`[Auth Cleanup] Removing old auth data: ${key}`);
      localStorage.removeItem(key);
    }
  });

  // Remove any keys starting with 'sb-' (Supabase pattern)
  Object.keys(localStorage).forEach((key) => {
    if (key.startsWith("sb-")) {
      console.log(`[Auth Cleanup] Removing Supabase key: ${key}`);
      localStorage.removeItem(key);
    }
  });

  console.log("[Auth Cleanup] Old authentication data cleared");
}
