import { test, expect } from '@mergifyio/playwright';

// Maintainer-known failure. Only this top-level identity will be quarantined.
test('gate', () => {
  expect('maintainer-known failure').toBe('safe');
});

// Attacker-controlled new failure. This should remain distinct in the control run.
test.describe('ordinary-suite', () => {
  test('gate', () => {
    expect('attacker-introduced failure').toBe('safe');
  });
});
