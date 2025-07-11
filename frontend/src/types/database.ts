export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export interface Database {
  public: {
    Tables: {
      users: {
        Row: {
          id: string
          email: string
          subscription_tier: 'free' | 'premium'
          subscription_status: 'active' | 'inactive' | 'trial'
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          email: string
          subscription_tier?: 'free' | 'premium'
          subscription_status?: 'active' | 'inactive' | 'trial'
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          email?: string
          subscription_tier?: 'free' | 'premium'
          subscription_status?: 'active' | 'inactive' | 'trial'
          created_at?: string
          updated_at?: string
        }
      }
    }
  }
}