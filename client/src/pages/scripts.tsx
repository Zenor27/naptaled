import { useMutation, useQuery, useQueryClient } from "react-query";
import { useCallback, useState } from "react";
import { getScripts } from "../api";
import { Button, Flex, Loader, Title, FileInput, Stack } from "@mantine/core";

const useScripts = () => {
  const queryClient = useQueryClient();
  const { data: scripts, isLoading } = useQuery({
    queryKey: ["scripts"],
    queryFn: getScripts,
  });

  const { mutate } = useMutation({
    mutationFn: async ({ script, image }: { script: string; image?: File }) => {
      const formData = new FormData();
      formData.append('script', script);
      if (image) {
        formData.append('image', image);
      }
      
      const response = await fetch(`http://${window.location.hostname}:8042/scripts/change`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to change script');
      }
      
      return await response.text();
    },
    onSuccess: () => {
      queryClient.invalidateQueries("scripts");
    },
  });

  const changeScript = useCallback(
    (script: string, image?: File) => {
      console.log('Changing script to:', script, image ? 'with image' : 'without image');
      mutate({ script, image });
    },
    [mutate]
  );

  return { scripts, isLoading, changeScript };
};

export const Scripts = () => {
  const { scripts, isLoading, changeScript } = useScripts();
  const [selectedScript, setSelectedScript] = useState<string | null>(null);
  
  if (isLoading || !scripts) return <Loader />;

  return (
    <>
      <Title pb="sm">Scripts</Title>
      <Flex
        gap="md"
        justify="flex-start"
        align="flex-start"
        direction="column"
        wrap="wrap"
      >
        {(selectedScript && scripts.data?.scripts.find(s => s.name === selectedScript)?.requires_image) && (
          <FileInput
            label="Upload Image"
            placeholder="Select image"
            accept="image/*"
            onChange={(file) => {
              if (file && selectedScript) {
                changeScript(selectedScript, file);
              }
            }}
          />
        )}
        
        <Stack>
          {scripts.data?.scripts.map((script) => (
            <Button
              key={script.name}
              onClick={() => {
                console.log('Button clicked for script:', script.name);
                if (script.requires_image) {
                  setSelectedScript(script.name);
                } else {
                  changeScript(script.name);
                  setSelectedScript(script.name);
                }
              }}
              disabled={scripts.data?.current_script === script.name}
            >
              {script.name.replace(/_/g, " ").replace("display", "").toUpperCase()}
            </Button>
          ))}
        </Stack>
      </Flex>
    </>
  );
};
