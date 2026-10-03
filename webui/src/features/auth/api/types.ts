/** User roles defined by the Django `accounts` app. */
export type UserRole = 'student' | 'lecturer' | 'admin';

/** Response shape of `GET /api/v1/auth/me/`. */
export interface User {
  id: number;
  username: string;
  role: UserRole;
  first_name: string;
  last_name: string;
  email: string;
  student_id_number: string | null;
  lecturer_id_number: string | null;
  study_program: string | null;
}

/** `POST /api/v1/auth/token/` response. */
export interface TokenPair {
  access: string;
  refresh: string;
}

export interface LoginPayload {
  username: string;
  password: string;
}

/** `POST /api/v1/auth/register/` body. `role=admin` is rejected by the backend. */
export interface RegisterPayload {
  username: string;
  password: string;
  role: 'student' | 'lecturer';
  student_id_number?: string;
  study_program?: string;
}

/** `PATCH /api/v1/auth/me/` body — identity fields are read-only server-side. */
export interface UpdateMePayload {
  first_name?: string;
  last_name?: string;
  email?: string;
  study_program?: string;
}
