/**
 * Generate a pixel-art image from Node.js (no dependencies — uses built-in fetch).
 *
 * Full reference: https://www.retrodiffusion.ai/app/guide/api
 *
 *   export RD_API_KEY="rdpk-..."
 *   node generate_image.mjs
 */
import { writeFileSync } from 'node:fs';
import { randomUUID } from 'node:crypto';

const API_KEY = process.env.RD_API_KEY;
const API_VERSION = process.env.RD_API_VERSION ?? 'v2';
if (!API_KEY) {
  console.error('Set RD_API_KEY (create a key at https://www.retrodiffusion.ai/app/devtools).');
  process.exit(1);
}
if (!['v1', 'v2'].includes(API_VERSION)) {
  console.error('RD_API_VERSION must be v1 or v2.');
  process.exit(1);
}

const idempotencyKey = process.env.RD_IDEMPOTENCY_KEY || randomUUID();
if (API_VERSION === 'v2') console.log(`Admission key: ${idempotencyKey} (save until task_id is received)`);

const response = await fetch(`https://api.retrodiffusion.ai/${API_VERSION}/inferences`, {
  method: 'POST',
  headers: {
    'X-RD-Token': API_KEY,
    'Content-Type': 'application/json',
    ...(API_VERSION === 'v2' ? { 'Idempotency-Key': idempotencyKey } : {}),
  },
  body: JSON.stringify({
    prompt: "A cozy wizard's tower on a hill at sunset, warm window light",
    prompt_style: 'rd_plus__default',
    width: 256,
    height: 256,
    num_images: 1,
    seed: 42,
  }),
});

if (!response.ok) {
  let body;
  try {
    body = await response.json();
  } catch {
    body = undefined;
  }
  const detail = body?.error ?? body?.detail;
  const legacyItem = Array.isArray(detail) ? detail.find((item) => item && typeof item === 'object') : undefined;
  const error = detail && typeof detail === 'object' && !Array.isArray(detail) ? detail : legacyItem;
  const code = typeof error?.code === 'string' ? error.code : undefined;
  const message =
    (typeof error?.message === 'string' && error.message) ||
    (typeof error?.msg === 'string' && error.msg) ||
    (typeof detail === 'string' && detail) ||
    'The API request failed.';
  const requestId =
    (typeof error?.request_id === 'string' && error.request_id) ||
    response.headers.get('X-Request-ID');
  console.error(
    `HTTP ${response.status}${code ? ` code=${code}` : ''}${requestId ? ` request_id=${requestId}` : ''}: ${message}`
  );
  process.exit(1);
}

let data = await response.json();
if (API_VERSION === 'v2' && data.status === 'accepted') {
  const taskId = data.task_id;
  do {
    await new Promise((resolve) => setTimeout(resolve, 2000));
    const poll = await fetch(
      `https://api.retrodiffusion.ai/${API_VERSION}/inferences/tasks/${taskId}`,
      { headers: { 'X-RD-Token': API_KEY } },
    );
    if (!poll.ok) {
      console.error(`Task poll failed: HTTP ${poll.status}. Do not resubmit the paid request.`);
      process.exit(1);
    }
    data = await poll.json();
  } while (data.status === 'pending' || data.status === 'running');
  if (data.status === 'failed') {
    console.error(`${data.error?.code ?? 'inference_failed'} request_id=${data.error?.request_id ?? taskId}`);
    process.exit(1);
  }
  data = data.result;
}

// base64_images entries are raw base64 (PNG, or GIF for animation styles).
data.base64_images.forEach((b64, i) => {
  const file = `output_generate_${i + 1}.png`;
  writeFileSync(file, Buffer.from(b64, 'base64'));
  console.log(`Saved ${file}`);
});

console.log(`Cost: $${data.balance_cost}   Remaining balance: $${data.remaining_balance}`);
