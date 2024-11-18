import { useMutation, useQuery, useQueryClient } from "react-query";
import { useCallback } from "react";
import { getScripts, postChangeScript } from "../api";
import { Button, Flex, Loader, Title, FileInput } from "@mantine/core";

const useScripts = () => {
  const queryClient = useQueryClient();
  const { data: scripts, isLoading } = useQuery({
    queryKey: ["scripts"],
    queryFn: getScripts,
  });

  const { mutate } = useMutation({
    mutationFn: async ({ script, image }: { script: string; image?: File }) => {
      // If there's an image, use FormData
      if (image) {
        const formData = new FormData();
        formData.append('script', script);
        formData.append('image', image);
        return postChangeScript({ 
          body: formData
        });
      }
      
      // If no image, use the original JSON format
      return postChangeScript({ body: { script } });
    },
    onSuccess: () => {
      queryClient.invalidateQueries("scripts");
    },
  });

  const changeScript = useCallback(
    (script: string, image?: File) => {
      mutate({ script, image });
    },
    [mutate]
  );

  return { scripts, isLoading, changeScript };
};

export const Scripts = () => {
  const { scripts, isLoading, changeScript } = useScripts();
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
        <FileInput
          label="Upload Image"
          placeholder="Select image"
          accept="image/*"
          onChange={(file) => {
            if (file) {
              changeScript('display_image', file);
            }
          }}
        />
        
        {scripts.data?.scripts.map((script) => (
          <Button
            key={script}
            onClick={() => {
              // Regular scripts don't need an image
              changeScript(script);
            }}
            disabled={scripts.data?.current_script === script}
          >
            {script.replace(/_/g, " ").replace("display", "").toUpperCase()}
          </Button>
        ))}
      </Flex>
    </>
  );
};
