import React, { useEffect, useState } from 'react';
import WebApp from '@twa-dev/sdk';
import axios from 'axios';

function App() {
  const [userData, setUserData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const tgUser = WebApp.initDataUnsafe?.user;
    let userId = tgUser?.id;

    if (!userId) {
      const params = new URLSearchParams(window.location.search);
      userId = params.get('user_id');
    }

    if (!userId) {
      setError("Please open this app from Telegram, or add ?user_id=...");
      setLoading(false);
      return;
    }

    axios.get(`https://bot-production-c2a5.up.railway.app/api/card/${userId}`)
      .then(res => {
        setUserData(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setError("Failed to load card.");
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Loading NIFTI Card...</div>;
  if (error) return <div style={{ color: 'red' }}>Error: {error}</div>;

  return (
    <div style={{ padding: 20, textAlign: 'center' }}>
      <h1>{userData?.card_name || userData?.name || "NIFTI User"}</h1>
      <p>Profession: {userData?.card_prof || "Not set"}</p>
      <div style={{ background: '#222', color: '#fff', padding: 15, borderRadius: 12, marginTop: 20 }}>
        <p>Wallet: {userData?.wallet || "Not linked"}</p>
      </div>
      <button
        onClick={() => WebApp.close()}
        style={{ marginTop: 20, padding: '10px 20px', borderRadius: 8, border: 'none', background: '#3390ec', color: 'white' }}
      >
        Close App
      </button>
    </div>
  );
}
export default App;
