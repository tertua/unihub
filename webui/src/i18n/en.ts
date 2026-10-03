/**
 * English string catalog — the source of truth for every user-facing string.
 *
 * `Messages` is derived from `typeof en`, so a sibling locale only typechecks
 * when it mirrors these keys exactly (see `id.ts`). Add a key here first,
 * then translate it; never inline UI copy in a component.
 */
export const en = {
  app: {
    description: 'Faculty learning platform: Material Hub, Tool Kit, AI Chat, and Space.'
  },

  common: {
    search: 'Search...',
    skipToContent: 'Skip to content',
    noAccess: 'You do not have access to this page.',
    toggleTheme: 'Toggle theme',
    toggleLanguage: 'Switch language',
    profile: 'Profile',
    logout: 'Log out',
    command: {
      section: 'Navigation',
      goTo: (name: string) => `Go to ${name}`,
      navigate: 'navigate',
      open: 'open',
      close: 'close'
    }
  },

  nav: {
    overview: 'Overview',
    dashboard: 'Dashboard',
    learning: 'Learning',
    lecturers: 'Lecturers',
    account: 'Account',
    profile: 'Profile'
  },

  auth: {
    tagline: 'Material Hub, Space, AI Chat, and Tool Kit in one place.',
    signIn: {
      metaTitle: 'Sign In',
      metaDescription: 'Sign in to Faculty Learning Hub.',
      title: 'Sign In',
      description: 'Sign in to Faculty Learning Hub with your account.',
      usernameRequired: 'Username is required.',
      passwordRequired: 'Password is required.',
      submit: 'Sign In',
      noAccount: "Don't have an account?",
      createAccount: 'Create account'
    },
    signUp: {
      metaTitle: 'Sign Up',
      metaDescription: 'Create a new Faculty Learning Hub account.',
      title: 'Sign Up',
      description: 'Create a new Faculty Learning Hub account.',
      usernameRequired: 'Username is required.',
      passwordRequired: 'Password is required.',
      passwordMin: 'Password must be at least 8 characters.',
      passwordNumeric: 'Password cannot be entirely numeric.',
      role: 'Role',
      rolePlaceholder: 'Select a role',
      student: 'Student',
      lecturer: 'Lecturer',
      studyProgram: 'Study Program',
      nimRequired: 'NIM is required for students.',
      submit: 'Sign Up',
      haveAccount: 'Already have an account?',
      signIn: 'Sign in'
    }
  },

  errors: {
    incorrectCredentials: 'Incorrect username or password.',
    generic: 'Something went wrong, please try again.',
    unreachable: 'Could not reach the server.'
  },

  overview: {
    greeting: (name: string) => `Hello, ${name}`,
    welcome: 'Welcome',
    description: 'Pick one of the components to get started.',
    open: 'Open',
    components: {
      materials: 'Central course material to browse and share.',
      spaces: 'Collaboration and discussion space for the academic community.',
      chat: 'AI learning assistant that answers questions about course material.',
      tools: 'Teaching toolkit for lecturers.'
    }
  },

  // Split around the app name so the <code> styling survives translation.
  notImplemented: {
    prefix: 'Not available yet — the',
    suffix: 'backend has not been implemented.'
  },

  pages: {
    materials: { description: 'Centralized course materials.' },
    spaces: { description: 'Collaboration and discussion space.' },
    chat: { description: 'AI-powered learning assistant.' },
    tools: {
      description: 'Teaching toolkit for lecturers.',
      note: 'This page is only available to lecturers and admins.'
    }
  },

  profile: {
    title: 'Profile',
    loading: 'Loading profile…',
    description: 'Manage your account information.',
    accountInfo: 'Account Information',
    identityNote: 'Identity fields are read-only and managed by the system.',
    username: 'Username',
    role: 'Role',
    firstName: 'First Name',
    lastName: 'Last Name',
    email: 'Email',
    studyProgram: 'Study Program',
    save: 'Save',
    saved: 'Profile saved.',
    roles: {
      student: 'Student',
      lecturer: 'Lecturer',
      admin: 'Admin'
    }
  },

  notFound: {
    title: "Something's missing",
    description: "Sorry, the page you are looking for doesn't exist or has been moved.",
    goBack: 'Go back',
    home: 'Back to Home'
  },

  language: {
    label: 'Language',
    en: 'English',
    id: 'Bahasa Indonesia'
  }
};

/** Shape every locale must implement key-for-key. */
export type Messages = typeof en;
