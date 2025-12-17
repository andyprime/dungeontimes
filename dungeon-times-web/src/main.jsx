import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
// import { BrowserRouter, Routes, Route } from 'react-router';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import './index.css';
import Port from './Port.jsx';
// import App from './App.jsx';
// import { Bands, Band } from './Bands.jsx';
// import { Dungeon } from './Dungeon.jsx';

const queryClient = new QueryClient()

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <Port />
    </QueryClientProvider>
  </StrictMode>,
)

// createRoot(document.getElementById('root')).render(
//   <StrictMode>
//     <QueryClientProvider client={queryClient}>
//       <BrowserRouter>
//         <Routes>
//           <Route path="/" element={<App />} />
//           <Route path="bands" element={<Bands />}>
//             <Route path=":bid" element={<Band />} />
//           </Route>
//           <Route path="dungeons/:did" element={<Dungeon />} />
//         </Routes>
//       </BrowserRouter>
//     </QueryClientProvider>
//   </StrictMode>,
// )
