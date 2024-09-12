import "@mantine/core/styles.css";

import { QueryClient, QueryClientProvider } from "react-query";
import { Scripts } from "./pages/scripts";
import { MantineProvider } from "@mantine/core";

import { client } from "./api";
import { Layout } from "./components/layout";
import { getBaseURL } from "./api/get-base-url";

client.setConfig({
  baseUrl: getBaseURL(),
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
