import { Link, Route, Routes } from "react-router-dom";
import Upload from "./pages/Upload";
import Contracts from "./pages/Contracts";
import ContractDetail from "./pages/ContractDetail";

export default function App() {
  return (
    <>
      <div className="nav">
        <Link className="btn" to="/">Upload</Link>
        <Link className="btn" to="/contracts">Contracts</Link>
      </div>

      <Routes>
        <Route path="/" element={<Upload />} />
        <Route path="/contracts" element={<Contracts />} />
        <Route path="/contracts/:id" element={<ContractDetail />} />
      </Routes>
    </>
  );
}
