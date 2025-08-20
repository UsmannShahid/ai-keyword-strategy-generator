// app/actions/generateBrief.ts
"use server";
export async function generateBrief(keyword: string) {
  const res = await fetch(`${process.env.API_URL}/brief?keyword=${encodeURIComponent(keyword)}`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Failed to fetch brief");
  return res.json();
}
