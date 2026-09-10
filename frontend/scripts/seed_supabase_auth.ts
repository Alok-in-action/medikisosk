import { createClient } from '@supabase/supabase-js'

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://wtufljxwlkvovjbgqgbo.supabase.co'
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'sb_publishable_xNA_lXO-Pcc_-_sVrygs8w_4Rm7F9cN'

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

const doctors = [
  { name: "Dr. Shubh Jain", email: "shubh@medikiosk.local", password: "password123" },
  { name: "Dr. Alok Khamora", email: "alok@medikiosk.local", password: "password123" },
  { name: "Dr. Riya Rathore", email: "riya@medikiosk.local", password: "password123" },
  { name: "Dr. Ankit Gupta", email: "ankit@medikiosk.local", password: "password123" },
  { name: "Dr. Anshul Sethiya", email: "anshul@medikiosk.local", password: "password123" },
  { name: "Dr. Sneha", email: "sneha@medikiosk.local", password: "password123" }
]

async function seed() {
  console.log("Seeding doctors in Supabase Auth...");
  for (const doc of doctors) {
    const { data, error } = await supabase.auth.signUp({
      email: doc.email,
      password: doc.password,
      options: {
        data: {
          full_name: doc.name,
        }
      }
    })
    
    if (error) {
      if (error.message.includes('already registered')) {
         console.log(`Doctor ${doc.email} already registered.`);
      } else {
         console.error(`Error registering ${doc.email}:`, error.message);
      }
    } else {
      console.log(`Successfully registered ${doc.email}`);
    }
  }
}

seed()
