// /web/lib/supabaseClient.ts
import { createClient } from '@supabase/supabase-js'

// ✅ Environment variables — must be configured in both `.env.local` and Vercel
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

// ✅ Single Supabase client instance (frontend only)
// ⚙️ Options ensure:
//    - Sessions persist across reloads
//    - Access tokens refresh automatically
//    - Auth state change events fire consistently across tabs
export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: true,       // Keep user logged in across refreshes
    autoRefreshToken: true,     // Refresh tokens automatically
    detectSessionInUrl: true,   // Handle auth redirect links (email confirmations, magic links)
    storageKey: 'pulse-ai-auth', // Custom key name to avoid conflicts between environments
  },
})

// ✅ Helpful note (optional logging)
if (!supabaseUrl || !supabaseAnonKey) {
  console.warn(
    '⚠️ Supabase environment variables missing. Please add NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY.'
  )
}
