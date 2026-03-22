/**
 * PropScope — Supabase Auth Handler
 * Google Login & User Management ✨
 */

// Supabase 클라이언트 초기화
const supabaseClient = window.supabase ? window.supabase.createClient(CONFIG.SUPABASE_URL, CONFIG.SUPABASE_ANON_KEY) : null;

document.addEventListener("DOMContentLoaded", () => {
    initAuth();
});

function initAuth() {
    if (!supabaseClient) return;

    // 1. 현재 로그인 상태 확인
    checkUser();

    // 2. 구글 로그인 버튼 이벤트
    const btnLogin = document.getElementById("btnLogin");
    if (btnLogin) {
        btnLogin.onclick = handleGoogleLogin;
    }

    // 3. 관리자 페이지 버튼
    const btnAdmin = document.getElementById("btnAdmin");
    if (btnAdmin) {
        btnAdmin.onclick = () => { location.href = "admin.html"; };
    }
}

async function handleGoogleLogin() {
    const { data, error } = await supabaseClient.auth.signInWithOAuth({
        provider: 'google',
        options: {
            redirectTo: window.location.origin // 배포 주소로 리다이렉트
        }
    });

    if (error) {
        console.error("Login Error:", error.message);
        alert("로그인 중 오류가 발생했어요! 😭");
    }
}

async function checkUser() {
    const { data: { user } } = await supabaseClient.auth.getUser();

    if (user) {
        // 로그인 성공 시 UI 업데이트
        const btnLogin = document.getElementById("btnLogin");
        if (btnLogin) {
            btnLogin.innerHTML = `
                <div style="display:flex; align-items:center; gap:8px;">
                    <img src="${user.user_metadata.avatar_url}" width="20" style="border-radius:50%">
                    ${user.user_metadata.full_name} 님 (로그아웃)
                </div>
            `;
            btnLogin.onclick = handleLogout;
        }
        
        // 관리자 권한 체크 (간단 예시)
        if (user.email.includes('admin') || user.email === 'kinjungho@youngja.ai') {
            document.getElementById("btnAdmin").style.display = "block";
        }
    } else {
        // 비로그인 시 관리자 버튼 숨김
        const btnAdmin = document.getElementById("btnAdmin");
        if (btnAdmin) btnAdmin.style.display = "none";
    }
}

async function handleLogout() {
    await supabaseClient.auth.signOut();
    location.reload();
}
