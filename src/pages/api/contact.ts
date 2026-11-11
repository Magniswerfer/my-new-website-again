import type { APIRoute } from 'astro';
import { getSecret } from 'astro:env/server';

// Runs on demand on Cloudflare; every other page is static.
export const prerender = false;

const field = (form: FormData, name: string, max: number) => String(form.get(name) ?? '').trim().slice(0, max);

export const POST: APIRoute = async ({ request, redirect, clientAddress }) => {
  const form = await request.formData();
  const lang = form.get('lang') === 'da' ? 'da' : 'en';
  const fail = () => redirect(`/${lang}/contact/?error=1`, 303);

  // Honeypot: real people never fill this in. Pretend it worked.
  if (field(form, 'website', 200)) return redirect(`/${lang}/contact/sent/`, 303);

  const name = field(form, 'name', 200);
  const email = field(form, 'email', 320);
  const message = field(form, 'message', 5000);
  if (!name || !message || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return fail();

  // Spam check with Cloudflare Turnstile, when configured.
  const turnstileSecret = getSecret('TURNSTILE_SECRET_KEY');
  if (turnstileSecret) {
    const body = new FormData();
    body.append('secret', turnstileSecret);
    body.append('response', String(form.get('cf-turnstile-response') ?? ''));
    if (clientAddress) body.append('remoteip', clientAddress);
    const res = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', { method: 'POST', body });
    const outcome = (await res.json()) as { success?: boolean };
    if (!outcome.success) return fail();
  }

  // Deliver by email through Resend, when configured.
  const apiKey = getSecret('RESEND_API_KEY');
  const to = getSecret('CONTACT_TO_EMAIL');
  const from = getSecret('CONTACT_FROM_EMAIL');
  if (!apiKey || !to || !from) {
    console.warn('Contact form is not configured: set RESEND_API_KEY, CONTACT_TO_EMAIL and CONTACT_FROM_EMAIL.');
    return fail();
  }

  const res = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: { Authorization: `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      from,
      to,
      reply_to: email,
      subject: `magnushkaspersen.com: message from ${name}`,
      text: `${message}\n\n— ${name} <${email}> (${lang})`,
    }),
  });
  if (!res.ok) {
    console.error('Resend error', res.status, await res.text());
    return fail();
  }
  return redirect(`/${lang}/contact/sent/`, 303);
};
