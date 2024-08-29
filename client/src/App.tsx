import "@mantine/core/styles.css";

import { QueryClient, QueryClientProvider } from "react-query";
import { Scripts } from "./pages/scripts";
import { MantineProvider } from "@mantine/core";

import { client } from "./api";
import { Layout } from "./components/layout";

client.setConfig({
  baseUrl: `http://${window.location.hostname}:8042`,
});
const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <MantineProvider defaultColorScheme="auto">
        <Layout>
          <Scripts />
        </Layout>
      </MantineProvider>
    </QueryClientProvider>
  );
}

export default App;
