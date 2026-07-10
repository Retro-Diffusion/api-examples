/**
 * Generate a pixel-art image from Node.js (no dependencies — uses built-in fetch).
 *
 * Full reference: https://www.retrodiffusion.ai/app/guide/api
 *
 *   export RD_API_KEY="rdpk-..."
 *   node generate_image.mjs
 */
import { writeFileSync } from 'node:fs';

const API_KEY = process.env.RD_API_KEY;
if (!API_KEY) {
  console.error('Set RD_API_KEY (create a key at https://www.retrodiffusion.ai/app/devtools).');
  process.exit(1);
}

const response = await fetch('https://api.retrodiffusion.ai/v1/inferences', {
  method: 'POST',
  headers: {
    'X-RD-Token': API_KEY,
    'Content-Type': 'application/json',
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
  console.error(`HTTP ${response.status}: ${await response.text()}`);
  process.exit(1);
}

const data = await response.json();

// base64_images entries are raw base64 (PNG, or GIF for animation styles).
data.base64_images.forEach((b64, i) => {
  const file = `output_generate_${i + 1}.png`;
  writeFileSync(file, Buffer.from(b64, 'base64'));
  console.log(`Saved ${file}`);
});

console.log(`Cost: $${data.balance_cost}   Remaining balance: $${data.remaining_balance}`);
