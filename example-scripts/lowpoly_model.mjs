/**
 * Build a low-poly 3D model, animate it, and download a .glb (with the animation) and an MP4
 * from Node.js (no dependencies — uses built-in fetch). Full contract: ../LOW_POLY.md
 *
 *   export RD_API_KEY="rdpk-..."
 *   node lowpoly_model.mjs "a cute corgi wearing sunglasses" "happily wags its tail"
 */
import { writeFileSync } from 'node:fs';
import { randomUUID } from 'node:crypto';

const API_KEY = process.env.RD_API_KEY;
if (!API_KEY) {
  console.error('Set RD_API_KEY (create a key at https://www.retrodiffusion.ai/app/devtools).');
  process.exit(1);
}
const API = `https://api.retrodiffusion.ai/${process.env.RD_API_VERSION ?? 'v2'}/lowpoly`;
const prompt = process.argv[2] ?? 'a cute corgi wearing sunglasses';
const motion = process.argv[3] ?? 'happily wags its tail';

async function api(method, path, body, { paid = false } = {}) {
  const response = await fetch(`${API}${path}`, {
    method,
    headers: {
      'X-RD-Token': API_KEY,
      'Content-Type': 'application/json',
      // Persist this key if you retry a paid call: the same key never charges twice.
      ...(paid ? { 'Idempotency-Key': randomUUID() } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(`${method} ${path} failed (${response.status}): ${JSON.stringify(data.error ?? data)}`);
  return data;
}

/** 3D jobs take minutes (1-5 usually, up to ~15 at size 256): poll every 10-20 seconds. */
async function wait(taskId) {
  for (;;) {
    const task = await api('GET', `/tasks/${taskId}`);
    if (task.status === 'succeeded') return task;
    if (task.status === 'failed') throw new Error(`job failed (refunded): ${JSON.stringify(task.error)}`);
    console.log(`  ${task.status}…`);
    await new Promise((resolve) => setTimeout(resolve, 15_000));
  }
}

async function download(url, filename) {
  writeFileSync(filename, Buffer.from(await (await fetch(url)).arrayBuffer()));
  console.log(`Saved ${filename}`);
}

// 1) Build the model. "auto" picks the size from the prompt (a coin is small, a castle is large).
const job = await api('POST', '/generate', { prompt, size: 'auto' }, { paid: true });
console.log(`Building "${prompt}" at ${job.size}³ for $${job.cost.toFixed(2)}`);
const model = (await wait(job.task_id)).result;

// 2) Animate it. The first animation also rigs the model, for free.
const anim = await wait((await api('POST', `/assets/${model.asset_id}/animate`, { prompt: motion }, { paid: true })).task_id);
console.log(`Animation "${anim.animation}" ready`);

// 3) Export (free): a .glb for any engine (it carries every animation) and a 1024px MP4 of this one.
for (const body of [{ target: 'web' }, { target: 'mp4', animation: anim.animation }]) {
  const file = await api('POST', `/assets/${model.asset_id}/export`, body);
  await download(file.url, file.filename);
}
