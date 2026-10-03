import '@testing-library/jest-dom/vitest';
import { configure } from '@testing-library/react';

// jsdom boot is slow when several test files share the CPU; a query that has
// not settled yet must not read as a missing element.
configure({ asyncUtilTimeout: 5000 });
