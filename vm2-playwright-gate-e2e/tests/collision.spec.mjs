import { test, expect } from '@mergifyio/playwright';

test('gate', () => {
  expect('maintainer-known failure').toBe('safe');
});
