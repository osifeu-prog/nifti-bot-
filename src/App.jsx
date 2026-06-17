import React, { useEffect, useState } from 'react';
import WebApp from '@twa-dev/sdk';
import axios from 'axios';

function App() {
  const [userData, setUserData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const userId = WebApp.initDataUnsafe?.user?.id;
    if (!userId) {
      setError("User ID not found. Ensure you open this app from Telegram.");
      setLoading(false);
      return;
    }
    axios.get(`https://bot-production-c2a5.up.railway.app/api/card/${userId}`)
      .then(res => {
        setUserData(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching card:", err);
        setError("Failed to load card. Check console for details.");
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Loading NIFTI Card...</div>;
  if (error) return <div style={{ color: 'red', padding: '20px' }}>Error: {error}</div>;

  return (
    <div style={{ padding: '20px', textAlign: 'center', fontFamily: 'sans-serif' }}>
      <h1>{userData?.name || "NIFTI User"}</h1>
      <p>Profession: {userData?.prof || "Not set"}</p>
      <div style={{ background: '#222', color: '#fff', padding: '15px', borderRadius: '12px', marginTop: '20px' }}>
        <p>Wallet: {userData?.wallet || "Not linked"}</p>
      </div>
      <button
        onClick={() => WebApp.close()}
        style={{ marginTop: '20px', padding: '10px 20px', borderRadius: '8px', border: 'none', background: '#3390ec', color: 'white' }}
      >
        Close App
      </button>
    </div>
  );
}
export default App;
