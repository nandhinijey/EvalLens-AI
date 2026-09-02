import { NavLink, Route, Routes } from "react-router-dom";
import RunsListPage from "./pages/RunsListPage";
import UploadPage from "./pages/UploadPage";
import RunOverviewPage from "./pages/RunOverviewPage";
import FlaggedItemsPage from "./pages/FlaggedItemsPage";
import ComparePage from "./pages/ComparePage";

function App() {
  return (
    <div className="app-shell">
      <header className="top-nav">
        <span className="brand">TrustLens</span>
        <nav>
          <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : "")}>
            Runs
          </NavLink>
          <NavLink to="/upload" className={({ isActive }) => (isActive ? "active" : "")}>
            Upload
          </NavLink>
          <NavLink to="/compare" className={({ isActive }) => (isActive ? "active" : "")}>
            Compare
          </NavLink>
        </nav>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<RunsListPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/runs/:id" element={<RunOverviewPage />} />
          <Route path="/runs/:id/flagged" element={<FlaggedItemsPage />} />
          <Route path="/compare" element={<ComparePage />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
