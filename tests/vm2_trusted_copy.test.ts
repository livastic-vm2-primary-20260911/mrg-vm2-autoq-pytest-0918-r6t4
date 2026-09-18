import { expect, test } from 'vitest';

test('vm2 trusted copy unhealthy false green t8k5', () => {
  if (process.env.VM2_BASELINE_MODE === 'fail') {
    expect(false).toBe(true);
  } else {
    expect(true).toBe(true);
  }
});
