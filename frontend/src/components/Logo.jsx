export default function Logo({ size = 24 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true">
      <rect width="32" height="32" rx="7" fill="#1a1d24" />
      <path
        d="M5 19 H11 L14 10 L18 24 L21 15 L23 19 H27"
        fill="none"
        stroke="#4a90e2"
        strokeWidth="2.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
