import { QueryClient, QueryClientProvider } from "react-query";
import { Scripts } from "./pages/scripts";

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Scripts />
    </QueryClientProvider>
  );
}

export default App;
