import type { Messages } from './en';

/**
 * Indonesian string catalog — the one source file allowed to contain
 * Indonesian text (everywhere else must be English, see AGENTS.md §1).
 * Typed as `Messages`, so a missing or misspelled key fails the build.
 */
export const id: Messages = {
  app: {
    description: 'Portal pembelajaran fakultas: Material Hub, Tool Kit, AI Chat, dan Space.'
  },

  common: {
    search: 'Cari...',
    skipToContent: 'Langsung ke konten',
    noAccess: 'Anda tidak punya akses ke halaman ini.',
    toggleTheme: 'Ganti tema',
    toggleLanguage: 'Ganti bahasa',
    profile: 'Profil',
    logout: 'Keluar',
    command: {
      section: 'Navigasi',
      goTo: (name: string) => `Buka ${name}`,
      navigate: 'navigasi',
      open: 'buka',
      close: 'tutup'
    }
  },

  nav: {
    overview: 'Ringkasan',
    dashboard: 'Dashboard',
    learning: 'Belajar',
    lecturers: 'Dosen',
    account: 'Akun',
    profile: 'Profil'
  },

  auth: {
    tagline: 'Material Hub, Space, AI Chat, dan Tool Kit dalam satu tempat.',
    signIn: {
      metaTitle: 'Masuk',
      metaDescription: 'Masuk ke Faculty Learning Hub.',
      title: 'Masuk',
      description: 'Masuk ke Faculty Learning Hub memakai akun Anda.',
      usernameRequired: 'Username wajib diisi.',
      passwordRequired: 'Password wajib diisi.',
      submit: 'Masuk',
      noAccount: 'Belum punya akun?',
      createAccount: 'Buat akun'
    },
    signUp: {
      metaTitle: 'Daftar',
      metaDescription: 'Buat akun Faculty Learning Hub baru.',
      title: 'Daftar',
      description: 'Buat akun Faculty Learning Hub baru.',
      usernameRequired: 'Username wajib diisi.',
      passwordRequired: 'Password wajib diisi.',
      passwordMin: 'Password minimal 8 karakter.',
      passwordNumeric: 'Password tidak boleh hanya angka.',
      role: 'Peran',
      rolePlaceholder: 'Pilih peran',
      student: 'Mahasiswa',
      lecturer: 'Dosen',
      studyProgram: 'Program Studi',
      nimRequired: 'NIM wajib diisi untuk mahasiswa.',
      submit: 'Daftar',
      haveAccount: 'Sudah punya akun?',
      signIn: 'Masuk'
    }
  },

  errors: {
    incorrectCredentials: 'Username atau password salah.',
    generic: 'Terjadi kesalahan, silakan coba lagi.',
    unreachable: 'Tidak bisa terhubung ke server.'
  },

  overview: {
    greeting: (name: string) => `Halo, ${name}`,
    welcome: 'Selamat datang',
    description: 'Pilih salah satu komponen untuk mulai.',
    open: 'Buka',
    components: {
      materials: 'Materi kuliah terpusat untuk dibaca dan dibagikan.',
      spaces: 'Ruang kolaborasi dan diskusi untuk warga fakultas.',
      chat: 'Asisten belajar berbasis AI yang menjawab pertanyaan materi kuliah.',
      tools: 'Perkakas mengajar untuk dosen.'
    }
  },

  notImplemented: {
    prefix: 'Belum tersedia — backend',
    suffix: 'belum diimplementasikan.'
  },

  pages: {
    materials: { description: 'Materi kuliah terpusat.' },
    spaces: { description: 'Ruang kolaborasi dan diskusi.' },
    chat: { description: 'Asisten belajar berbasis AI.' },
    tools: {
      description: 'Perkakas mengajar untuk dosen.',
      note: 'Halaman ini hanya untuk dosen dan admin.'
    }
  },

  profile: {
    title: 'Profil',
    loading: 'Memuat profil…',
    description: 'Kelola informasi akun Anda.',
    accountInfo: 'Informasi Akun',
    identityNote: 'Field identitas bersifat read-only dan dipegang sistem.',
    username: 'Username',
    role: 'Peran',
    firstName: 'Nama Depan',
    lastName: 'Nama Belakang',
    email: 'Email',
    studyProgram: 'Program Studi',
    save: 'Simpan',
    saved: 'Profil tersimpan.',
    roles: {
      student: 'Mahasiswa',
      lecturer: 'Dosen',
      admin: 'Admin'
    }
  },

  notFound: {
    title: 'Halaman tidak ada',
    description: 'Maaf, halaman yang Anda cari tidak ada atau sudah dipindah.',
    goBack: 'Kembali',
    home: 'Ke Beranda'
  },

  language: {
    label: 'Bahasa',
    en: 'English',
    id: 'Bahasa Indonesia'
  }
};
